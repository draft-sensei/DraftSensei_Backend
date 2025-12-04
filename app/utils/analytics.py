"""
Analytics Utility - Performance analytics and insights
"""

from typing import Dict, List, Any, Tuple, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, text
from datetime import datetime, timedelta
import statistics

from ..db.models import Hero, MatchHistory, PlayerPreference


class DraftAnalytics:
    """
    Analytics engine for draft performance and insights
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def get_hero_performance_stats(self, days: int = 30, min_matches: int = 5) -> List[Dict[str, Any]]:
        """
        Get hero performance statistics over the specified period
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Query hero performance data
        stats = (
            self.db.query(
                Hero.name,
                Hero.role,
                func.avg(MatchHistory.performance_score).label('avg_performance'),
                func.count(MatchHistory.id).label('match_count'),
                func.stddev(MatchHistory.performance_score).label('performance_std'),
                func.min(MatchHistory.performance_score).label('min_performance'),
                func.max(MatchHistory.performance_score).label('max_performance')
            )
            .join(MatchHistory, Hero.id == MatchHistory.hero_id)
            .filter(MatchHistory.timestamp >= cutoff_date)
            .group_by(Hero.id, Hero.name, Hero.role)
            .having(func.count(MatchHistory.id) >= min_matches)
            .order_by(desc('avg_performance'))
            .all()
        )
        
        performance_stats = []
        for stat in stats:
            performance_stats.append({
                'hero': stat.name,
                'role': stat.role,
                'avg_performance': round(stat.avg_performance, 2),
                'match_count': stat.match_count,
                'performance_std': round(stat.performance_std or 0, 2),
                'min_performance': round(stat.min_performance, 2),
                'max_performance': round(stat.max_performance, 2),
                'consistency_score': self._calculate_consistency_score(
                    stat.avg_performance, stat.performance_std or 0
                )
            })
        
        return performance_stats
    
    def get_role_meta_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze meta trends by role
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        role_stats = (
            self.db.query(
                Hero.role,
                func.avg(MatchHistory.performance_score).label('avg_performance'),
                func.count(MatchHistory.id).label('total_matches'),
                func.count(func.distinct(Hero.id)).label('unique_heroes')
            )
            .join(MatchHistory, Hero.id == MatchHistory.hero_id)
            .filter(MatchHistory.timestamp >= cutoff_date)
            .group_by(Hero.role)
            .all()
        )
        
        meta_analysis = {
            'period_days': days,
            'roles': {},
            'summary': {}
        }
        
        total_matches = sum(stat.total_matches for stat in role_stats)
        
        for stat in role_stats:
            role_data = {
                'avg_performance': round(stat.avg_performance, 2),
                'total_matches': stat.total_matches,
                'unique_heroes': stat.unique_heroes,
                'pick_rate': round((stat.total_matches / total_matches) * 100, 2),
                'diversity_score': round(stat.total_matches / stat.unique_heroes, 2)
            }
            meta_analysis['roles'][stat.role] = role_data
        
        # Overall summary
        meta_analysis['summary'] = {
            'total_matches': total_matches,
            'most_picked_role': max(role_stats, key=lambda x: x.total_matches).role,
            'best_performing_role': max(role_stats, key=lambda x: x.avg_performance).role,
            'most_diverse_role': min(role_stats, key=lambda x: x.total_matches / x.unique_heroes).role
        }
        
        return meta_analysis
    
    def get_counter_effectiveness(self, hero_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze how effectively heroes counter the specified hero
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get matches where the hero was played
        target_hero = self.db.query(Hero).filter(Hero.name == hero_name).first()
        if not target_hero:
            return {"error": f"Hero '{hero_name}' not found"}
        
        # Get match data where this hero was in enemy composition
        matches = (
            self.db.query(MatchHistory)
            .filter(
                and_(
                    MatchHistory.timestamp >= cutoff_date,
                    MatchHistory.enemy_composition.contains(f'"{hero_name}"')
                )
            )
            .all()
        )
        
        counter_data = {}
        
        for match in matches:
            ally_heroes = match.get_ally_composition()
            for ally_hero in ally_heroes:
                if ally_hero not in counter_data:
                    counter_data[ally_hero] = {
                        'matches': 0,
                        'total_performance': 0,
                        'avg_performance': 0
                    }
                
                counter_data[ally_hero]['matches'] += 1
                counter_data[ally_hero]['total_performance'] += match.performance_score
        
        # Calculate averages
        for hero, data in counter_data.items():
            if data['matches'] > 0:
                data['avg_performance'] = round(data['total_performance'] / data['matches'], 2)
        
        # Sort by effectiveness (high performance against target hero)
        effective_counters = sorted(
            [(hero, data) for hero, data in counter_data.items() if data['matches'] >= 3],
            key=lambda x: x[1]['avg_performance'],
            reverse=True
        )
        
        return {
            'target_hero': hero_name,
            'analysis_period': days,
            'effective_counters': effective_counters[:10],
            'total_matchups': len(counter_data)
        }
    
    def get_synergy_analysis(self, hero_name: str, days: int = 30) -> Dict[str, Any]:
        """
        Analyze synergy effectiveness for a hero
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        target_hero = self.db.query(Hero).filter(Hero.name == hero_name).first()
        if not target_hero:
            return {"error": f"Hero '{hero_name}' not found"}
        
        # Get matches where this hero was played
        matches = (
            self.db.query(MatchHistory)
            .filter(
                and_(
                    MatchHistory.hero_id == target_hero.id,
                    MatchHistory.timestamp >= cutoff_date
                )
            )
            .all()
        )
        
        synergy_data = {}
        
        for match in matches:
            ally_heroes = match.get_ally_composition()
            # Remove the hero itself from allies
            ally_heroes = [h for h in ally_heroes if h != hero_name]
            
            for ally in ally_heroes:
                if ally not in synergy_data:
                    synergy_data[ally] = {
                        'matches': 0,
                        'total_performance': 0,
                        'avg_performance': 0,
                        'performances': []
                    }
                
                synergy_data[ally]['matches'] += 1
                synergy_data[ally]['total_performance'] += match.performance_score
                synergy_data[ally]['performances'].append(match.performance_score)
        
        # Calculate statistics
        for ally, data in synergy_data.items():
            if data['matches'] > 0:
                data['avg_performance'] = round(data['total_performance'] / data['matches'], 2)
                if len(data['performances']) > 1:
                    data['performance_std'] = round(statistics.stdev(data['performances']), 2)
                else:
                    data['performance_std'] = 0.0
                
                # Remove raw performances to save space
                del data['performances']
        
        # Best synergy partners (high performance, multiple matches)
        best_partners = sorted(
            [(ally, data) for ally, data in synergy_data.items() if data['matches'] >= 3],
            key=lambda x: x[1]['avg_performance'],
            reverse=True
        )
        
        return {
            'target_hero': hero_name,
            'analysis_period': days,
            'best_partners': best_partners[:10],
            'total_partners': len(synergy_data)
        }
    
    def get_draft_phase_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Analyze performance by draft phase/timing
        """
        # This would require additional match data about pick order
        # For now, return a placeholder structure
        return {
            'early_game_heroes': [],
            'mid_game_heroes': [],
            'late_game_heroes': [],
            'flexible_picks': []
        }
    
    def get_player_insights(self, player_id: str) -> Dict[str, Any]:
        """
        Get insights for a specific player
        """
        preferences = (
            self.db.query(PlayerPreference)
            .filter(PlayerPreference.player_id == player_id)
            .all()
        )
        
        if not preferences:
            return {"error": f"No data found for player '{player_id}'"}
        
        # Calculate player statistics
        total_games = sum(pref.play_count for pref in preferences)
        weighted_winrate = sum(pref.win_rate * pref.play_count for pref in preferences) / total_games if total_games > 0 else 0
        
        # Most played heroes
        most_played = sorted(preferences, key=lambda x: x.play_count, reverse=True)[:5]
        
        # Best performing heroes (min 5 games)
        best_performing = sorted(
            [pref for pref in preferences if pref.play_count >= 5],
            key=lambda x: x.win_rate,
            reverse=True
        )[:5]
        
        # Role distribution
        hero_roles = {}
        for pref in preferences:
            hero = self.db.query(Hero).filter(Hero.id == pref.hero_id).first()
            if hero:
                role = hero.role
                if role not in hero_roles:
                    hero_roles[role] = {'games': 0, 'heroes': 0}
                hero_roles[role]['games'] += pref.play_count
                hero_roles[role]['heroes'] += 1
        
        return {
            'player_id': player_id,
            'overview': {
                'total_games': total_games,
                'overall_winrate': round(weighted_winrate, 2),
                'unique_heroes': len(preferences),
                'most_played_role': max(hero_roles.items(), key=lambda x: x[1]['games'])[0] if hero_roles else None
            },
            'most_played_heroes': [
                {
                    'hero_id': pref.hero_id,
                    'games': pref.play_count,
                    'winrate': round(pref.win_rate, 2)
                }
                for pref in most_played
            ],
            'best_performing_heroes': [
                {
                    'hero_id': pref.hero_id,
                    'games': pref.play_count,
                    'winrate': round(pref.win_rate, 2)
                }
                for pref in best_performing
            ],
            'role_distribution': hero_roles
        }
    
    def get_meta_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get overall meta trends and insights
        """
        performance_stats = self.get_hero_performance_stats(days)
        role_analysis = self.get_role_meta_analysis(days)
        
        # Identify trend categories
        s_tier = [hero for hero in performance_stats if hero['avg_performance'] >= 80 and hero['match_count'] >= 10]
        a_tier = [hero for hero in performance_stats if 70 <= hero['avg_performance'] < 80 and hero['match_count'] >= 8]
        rising = [hero for hero in performance_stats if hero['avg_performance'] >= 75 and hero['consistency_score'] >= 80]
        
        return {
            'analysis_period': days,
            'tier_rankings': {
                'S': s_tier[:5],
                'A': a_tier[:8],
            },
            'trending': {
                'rising_heroes': rising[:5],
                'consistent_performers': sorted(performance_stats, key=lambda x: x['consistency_score'], reverse=True)[:5]
            },
            'role_meta': role_analysis,
            'insights': self._generate_meta_insights(performance_stats, role_analysis)
        }
    
    def _calculate_consistency_score(self, avg_performance: float, std_dev: float) -> float:
        """
        Calculate consistency score (higher is more consistent)
        """
        if std_dev == 0:
            return 100.0
        
        # Penalize high standard deviation
        consistency = max(0, 100 - (std_dev / avg_performance * 100))
        return round(consistency, 2)
    
    def _generate_meta_insights(self, performance_stats: List[Dict], role_analysis: Dict) -> List[str]:
        """
        Generate textual insights about the current meta
        """
        insights = []
        
        if performance_stats:
            top_hero = performance_stats[0]
            insights.append(f"{top_hero['hero']} dominates the meta with {top_hero['avg_performance']}% average performance")
        
        if 'summary' in role_analysis:
            best_role = role_analysis['summary']['most_picked_role']
            insights.append(f"{best_role} role has the highest pick rate in the current meta")
        
        # Check for role diversity
        role_counts = role_analysis.get('roles', {})
        if len(role_counts) > 0:
            pick_rates = [data['pick_rate'] for data in role_counts.values()]
            if max(pick_rates) - min(pick_rates) > 10:
                insights.append("Meta shows significant role imbalance")
            else:
                insights.append("Role distribution is relatively balanced")
        
        return insights


def generate_daily_report(db_session: Session, days: int = 7) -> Dict[str, Any]:
    """
    Generate a comprehensive daily meta report
    """
    analytics = DraftAnalytics(db_session)
    
    report = {
        'report_date': datetime.now().isoformat(),
        'period': f"Last {days} days",
        'meta_trends': analytics.get_meta_trends(days),
        'top_performers': analytics.get_hero_performance_stats(days, min_matches=5)[:10],
        'role_analysis': analytics.get_role_meta_analysis(days)
    }
    
    return report


if __name__ == "__main__":
    # Example usage
    from ..db.database import SessionLocal
    
    db = SessionLocal()
    try:
        analytics = DraftAnalytics(db)
        
        # Generate sample reports
        meta_trends = analytics.get_meta_trends(30)
        print("Meta Trends:", meta_trends)
        
        hero_stats = analytics.get_hero_performance_stats(30)
        print("Hero Performance:", hero_stats[:5])
        
    finally:
        db.close()