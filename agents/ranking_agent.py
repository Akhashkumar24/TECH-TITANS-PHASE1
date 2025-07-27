# agents/ranking_agent.py
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.agent_protocol import AgentMessage, MessageType
from config.database import db_connection
from models.ranking import Ranking
from utils.logger import get_logger
import json
import time

class RankingAgent(BaseAgent):
    def __init__(self, protocol):
        super().__init__("ranking_agent", protocol)
        
        # Send periodic heartbeats to maintain A2A connection
        self._start_heartbeat()
        
    def _start_heartbeat(self):
        """Start heartbeat to maintain agent status"""
        import threading
        def heartbeat_loop():
            while True:
                try:
                    self.protocol.send_heartbeat(self.name)
                    time.sleep(30)  # Heartbeat every 30 seconds
                except Exception as e:
                    self.logger.error(f"Heartbeat error: {e}")
                    time.sleep(30)
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
    
    def receive_message(self, message: AgentMessage):
        """Process incoming messages following A2A protocol"""
        try:
            self.logger.info(f"Received message from {message.sender}: {message.message_type.value}")
            
            if message.message_type == MessageType.REQUEST:
                if message.payload.get('action') == 'rank_applications':
                    result = self.rank_applications(message.payload)
                    
                    # Send response back to sender
                    self.send_message(
                        message.sender,
                        MessageType.RESPONSE,
                        result,
                        message.message_id
                    )
                    
                    # If ranking was successful, notify communication agent with rankings
                    if result['status'] == 'success' and result.get('rankings'):
                        self.logger.info("Sending ranking results to communication agent")
                        
                        # Create communication message with ranking data
                        comm_message = AgentMessage(
                            sender=self.name,
                            receiver='communication_agent',
                            message_type=MessageType.REQUEST,
                            payload={
                                'action': 'send_ranking_notification',
                                'job_id': message.payload.get('job_id'),
                                'rankings': result.get('rankings', [])
                            },
                            correlation_id=message.message_id
                        )
                        
                        # Send to communication agent
                        comm_success = self.protocol.send_message(comm_message)
                        if comm_success:
                            self.logger.info("Successfully sent rankings to communication agent")
                        else:
                            self.logger.error("Failed to send rankings to communication agent")
                        
                else:
                    # Unknown action
                    error_result = {'status': 'error', 'message': f'Unknown action: {message.payload.get("action")}'}
                    self.send_message(
                        message.sender,
                        MessageType.ERROR,
                        error_result,
                        message.message_id
                    )
                    
            elif message.message_type == MessageType.NOTIFICATION:
                # Handle notifications from other agents
                self.handle_notification(message.payload)
                
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            # Send error response
            self.send_message(
                message.sender,
                MessageType.ERROR,
                {'status': 'error', 'message': str(e)},
                message.message_id
            )
    
    def handle_notification(self, payload: Dict[str, Any]):
        """Handle notifications from other agents"""
        notification_type = payload.get('event_type')
        
        if notification_type == 'agent_registered':
            agent_name = payload.get('agent_name')
            self.logger.info(f"New agent registered: {agent_name}")
        elif notification_type == 'agent_unregistered':
            agent_name = payload.get('agent_name')
            self.logger.info(f"Agent unregistered: {agent_name}")
    
    def process_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process ranking task"""
        return self.rank_applications(task_data)
    
    def rank_applications(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Rank applications based on comparison results with enhanced scoring"""
        job_id = task_data.get('job_id')
        comparison_results = task_data.get('comparison_results', [])
        
        if not job_id:
            return {'status': 'error', 'message': 'Job ID required'}
        
        if not comparison_results:
            self.logger.warning(f"No comparison results provided for job {job_id}")
            return {'status': 'error', 'message': 'No comparison results to rank'}
        
        try:
            self.logger.info(f"Ranking {len(comparison_results)} applications for job {job_id}")
            
            # Enhanced ranking with multiple criteria
            scored_results = []
            for result in comparison_results:
                enhanced_score = self._calculate_enhanced_score(result)
                result['enhanced_score'] = enhanced_score
                scored_results.append(result)
            
            # Sort applications by enhanced score (descending)
            ranked_results = sorted(
                scored_results,
                key=lambda x: x.get('enhanced_score', 0),
                reverse=True
            )
            
            # Clear existing rankings for this job
            self._clear_existing_rankings(job_id)
            
            # Save new rankings to database
            rankings = []
            for i, result in enumerate(ranked_results, 1):
                similarity_score = result.get('similarity_score', 0.0)
                enhanced_score = result.get('enhanced_score', similarity_score)
                comparison_details = result.get('comparison_details', {})
                
                # Ensure scores are valid floats
                try:
                    similarity_score = float(similarity_score) if similarity_score is not None else 0.0
                    enhanced_score = float(enhanced_score) if enhanced_score is not None else similarity_score
                except (ValueError, TypeError):
                    self.logger.warning(f"Invalid score values for application {result.get('application_id')}")
                    similarity_score = 0.0
                    enhanced_score = 0.0
                
                # Add ranking metadata to comparison details
                if not isinstance(comparison_details, dict):
                    comparison_details = {}
                
                comparison_details['ranking_metadata'] = {
                    'original_similarity_score': similarity_score,
                    'enhanced_score': enhanced_score,
                    'rank_position': i,
                    'total_candidates': len(ranked_results),
                    'ranking_timestamp': time.time()
                }
                
                ranking = Ranking(
                    job_id=job_id,
                    application_id=result['application_id'],
                    similarity_score=enhanced_score,  # Use enhanced score
                    rank_position=i,
                    ranking_details=comparison_details
                )
                
                ranking_id = self._save_ranking(ranking)
                if ranking_id:
                    ranking.id = ranking_id
                    ranking.applicant_name = result.get('applicant_name', 'Unknown')
                    rankings.append(ranking)
                    
                    self.logger.info(f"Saved ranking {i} for application {result['application_id']} with enhanced score {enhanced_score:.3f}")
                else:
                    self.logger.error(f"Failed to save ranking for application {result['application_id']}")
            
            if not rankings:
                self.logger.error("No rankings were successfully saved to database")
                return {
                    'status': 'error',
                    'message': 'Failed to save rankings to database',
                    'job_id': job_id,
                    'rankings': []
                }
            
            # Generate ranking insights
            insights = self._generate_ranking_insights(rankings)
            
            # Log the ranking completion
            self.log_activity('ranking_completed', {
                'job_id': job_id,
                'total_ranked': len(rankings),
                'avg_score': sum(r.similarity_score for r in rankings) / len(rankings) if rankings else 0
            })
            
            # Format rankings for response - include all necessary data
            formatted_rankings = []
            for r in rankings:
                formatted_rankings.append({
                    'rank': r.rank_position,
                    'applicant_name': r.applicant_name,
                    'similarity_score': r.similarity_score,
                    'application_id': r.application_id,
                    'enhanced_score': r.ranking_details.get('ranking_metadata', {}).get('enhanced_score', r.similarity_score),
                    'ranking_details': r.ranking_details
                })
            
            self.logger.info(f"Successfully ranked {len(formatted_rankings)} applications for job {job_id}")
            
            return {
                'status': 'success',
                'job_id': job_id,
                'total_ranked': len(rankings),
                'insights': insights,
                'rankings': formatted_rankings
            }
            
        except Exception as e:
            self.logger.error(f"Error in ranking process: {e}")
            return {
                'status': 'error', 
                'message': str(e),
                'job_id': job_id,
                'rankings': []
            }
    
    def _calculate_enhanced_score(self, result: Dict[str, Any]) -> float:
        """Calculate enhanced score considering multiple factors"""
        try:
            base_score = result.get('similarity_score', 0.0)
            if base_score is None:
                base_score = 0.0
            
            base_score = float(base_score)
            comparison_details = result.get('comparison_details', {})
            
            if not isinstance(comparison_details, dict):
                self.logger.warning(f"Invalid comparison_details for result: {result.get('application_id')}")
                return base_score
            
            enhanced_score = base_score
            
            # Skills matching bonus/penalty
            skills_match = comparison_details.get('skills_match', {})
            if isinstance(skills_match, dict):
                matched_skills = skills_match.get('matched_skills', [])
                missing_skills = skills_match.get('missing_skills', [])
                
                if isinstance(matched_skills, list) and len(matched_skills) > 0:
                    skills_bonus = min(0.1, len(matched_skills) * 0.02)  # Up to 10% bonus
                    enhanced_score += skills_bonus
                
                if isinstance(missing_skills, list) and len(missing_skills) > 0:
                    skills_penalty = min(0.1, len(missing_skills) * 0.015)  # Up to 10% penalty
                    enhanced_score -= skills_penalty
            
            # Experience relevance bonus
            experience_match = comparison_details.get('experience_match', {})
            if isinstance(experience_match, dict):
                relevance_score = experience_match.get('relevance_score', 0)
                try:
                    relevance_score = float(relevance_score)
                    if relevance_score > 0.7:
                        enhanced_score += 0.05  # 5% bonus for high experience relevance
                except (ValueError, TypeError):
                    pass
            
            # Education match bonus
            education_match = comparison_details.get('education_match', {})
            if isinstance(education_match, dict):
                meets_requirements = education_match.get('meets_requirements', False)
                if meets_requirements:
                    enhanced_score += 0.03  # 3% bonus for meeting education requirements
            
            # Overall assessment impact
            overall_assessment = comparison_details.get('overall_assessment', {})
            if isinstance(overall_assessment, dict):
                recommendation = overall_assessment.get('recommendation', '')
                
                if recommendation == 'highly_recommended':
                    enhanced_score += 0.08
                elif recommendation == 'recommended':
                    enhanced_score += 0.04
                elif recommendation == 'not_recommended':
                    enhanced_score -= 0.05
            
            # Ensure score stays within bounds
            enhanced_score = max(0.0, min(1.0, enhanced_score))
            
            return enhanced_score
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced score: {e}")
            base_score = result.get('similarity_score', 0.0)
            try:
                return float(base_score) if base_score is not None else 0.0
            except (ValueError, TypeError):
                return 0.0
    
    def _generate_ranking_insights(self, rankings: List[Ranking]) -> Dict[str, Any]:
        """Generate insights about the ranking results"""
        if not rankings:
            return {'message': 'No rankings available for analysis'}
        
        try:
            total_candidates = len(rankings)
            scores = [r.similarity_score for r in rankings if r.similarity_score is not None]
            
            if not scores:
                return {'message': 'No valid scores available for analysis'}
            
            avg_score = sum(scores) / len(scores)
            
            # Quality distribution
            high_quality = sum(1 for score in scores if score > 0.7)
            good_quality = sum(1 for score in scores if 0.5 <= score <= 0.7)
            low_quality = sum(1 for score in scores if score < 0.5)
            
            # Top performer analysis
            top_candidate = rankings[0] if rankings else None
            top_score = top_candidate.similarity_score if top_candidate and top_candidate.similarity_score else 0
            
            # Recommendation thresholds
            recommended_count = sum(1 for r in rankings if r.similarity_score and r.similarity_score > 0.6)
            
            insights = {
                'summary': {
                    'total_candidates': total_candidates,
                    'average_score': round(avg_score, 3),
                    'top_score': round(float(top_score), 3),
                    'recommended_candidates': recommended_count
                },
                'quality_distribution': {
                    'high_quality': high_quality,  # > 70%
                    'good_quality': good_quality,   # 50-70%
                    'low_quality': low_quality      # < 50%
                },
                'recommendations': self._generate_hiring_recommendations(rankings),
                'trends': {
                    'score_variance': round(self._calculate_variance(scores), 3),
                    'quality_ratio': round(high_quality / total_candidates, 3) if total_candidates > 0 else 0
                }
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return {'message': f'Error generating insights: {str(e)}'}
    
    def _generate_hiring_recommendations(self, rankings: List[Ranking]) -> List[str]:
        """Generate hiring recommendations based on ranking results"""
        recommendations = []
        
        if not rankings:
            return ['No candidates to evaluate']
        
        top_candidates = [r for r in rankings if r.similarity_score and r.similarity_score > 0.7]
        good_candidates = [r for r in rankings if r.similarity_score and 0.5 <= r.similarity_score <= 0.7]
        
        if len(top_candidates) >= 3:
            recommendations.append(f"Excellent candidate pool: {len(top_candidates)} high-quality matches found")
            recommendations.append("Recommend interviewing top 3-5 candidates")
        elif len(top_candidates) > 0:
            recommendations.append(f"Found {len(top_candidates)} high-quality candidate(s)")
            if len(good_candidates) > 0:
                recommendations.append(f"Consider {len(good_candidates)} additional candidates for backup")
        elif len(good_candidates) > 0:
            recommendations.append(f"Moderate candidate pool: {len(good_candidates)} decent matches")
            recommendations.append("Consider expanding search or reviewing job requirements")
        else:
            recommendations.append("Limited candidate pool - consider:")
            recommendations.append("• Revising job requirements")
            recommendations.append("• Expanding recruitment channels")
            recommendations.append("• Offering training for skill gaps")
        
        return recommendations
    
    def _calculate_variance(self, scores: List[float]) -> float:
        """Calculate variance of scores"""
        if len(scores) < 2:
            return 0.0
        
        try:
            mean = sum(scores) / len(scores)
            variance = sum((score - mean) ** 2 for score in scores) / len(scores)
            return variance
        except Exception as e:
            self.logger.error(f"Error calculating variance: {e}")
            return 0.0
    
    def _clear_existing_rankings(self, job_id: int):
        """Clear existing rankings for a job"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("DELETE FROM rankings WHERE job_id = %s", (job_id,))
                self.logger.info(f"Cleared existing rankings for job {job_id}")
        except Exception as e:
            self.logger.error(f"Error clearing existing rankings: {e}")
    
    def _save_ranking(self, ranking: Ranking) -> int:
        """Save ranking to database with proper JSON serialization"""
        try:
            with db_connection.get_cursor() as cursor:
                # Convert ranking_details to JSON string if it's a dict
                ranking_details_json = None
                if ranking.ranking_details:
                    if isinstance(ranking.ranking_details, dict):
                        ranking_details_json = json.dumps(ranking.ranking_details)
                    elif isinstance(ranking.ranking_details, str):
                        # Try to parse and re-serialize to ensure valid JSON
                        try:
                            parsed = json.loads(ranking.ranking_details)
                            ranking_details_json = json.dumps(parsed)
                        except json.JSONDecodeError:
                            # If it's not valid JSON, treat as plain text
                            ranking_details_json = json.dumps({"raw_text": ranking.ranking_details})
                    else:
                        # Convert other types to JSON
                        ranking_details_json = json.dumps(str(ranking.ranking_details))
                
                # Ensure similarity_score is a valid float
                try:
                    similarity_score = float(ranking.similarity_score) if ranking.similarity_score is not None else 0.0
                except (ValueError, TypeError):
                    similarity_score = 0.0
                    self.logger.warning(f"Invalid similarity_score for ranking, using 0.0")
                
                cursor.execute("""
                    INSERT INTO rankings (job_id, application_id, similarity_score, 
                                        rank_position, ranking_details)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    ranking.job_id,
                    ranking.application_id,
                    similarity_score,
                    ranking.rank_position,
                    ranking_details_json
                ))
                
                result = cursor.fetchone()
                if result:
                    self.logger.info(f"Successfully saved ranking with ID {result['id']}")
                    return result['id']
                else:
                    self.logger.error("Failed to save ranking - no ID returned")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error saving ranking: {e}")
            return None
    
    def get_ranking_statistics(self, job_id: int) -> Dict[str, Any]:
        """Get detailed statistics for job rankings"""
        try:
            with db_connection.get_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_rankings,
                        AVG(similarity_score) as avg_score,
                        MAX(similarity_score) as max_score,
                        MIN(similarity_score) as min_score,
                        COUNT(*) FILTER (WHERE similarity_score > 0.7) as high_quality,
                        COUNT(*) FILTER (WHERE similarity_score BETWEEN 0.5 AND 0.7) as medium_quality,
                        COUNT(*) FILTER (WHERE similarity_score < 0.5) as low_quality
                    FROM rankings 
                    WHERE job_id = %s
                """, (job_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'total_rankings': result['total_rankings'],
                        'average_score': float(result['avg_score']) if result['avg_score'] else 0.0,
                        'max_score': float(result['max_score']) if result['max_score'] else 0.0,
                        'min_score': float(result['min_score']) if result['min_score'] else 0.0,
                        'high_quality_count': result['high_quality'],
                        'medium_quality_count': result['medium_quality'],
                        'low_quality_count': result['low_quality']
                    }
                else:
                    return {'error': 'No rankings found for job'}
                    
        except Exception as e:
            self.logger.error(f"Error getting ranking statistics: {e}")
            return {'error': str(e)}