import os
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid


def get_db_connection():
    """Get database connection using environment variables."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))


def init_database():
    """Initialize database schema for property evaluations."""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Create evaluations table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id VARCHAR(255) NOT NULL,
                flow VARCHAR(50) NOT NULL,
                address TEXT NOT NULL,
                property_data JSONB NOT NULL,
                market_stats JSONB,
                evaluation_data JSONB NOT NULL,
                assumptions JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on session_id for faster lookups
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_session_id 
            ON evaluations(session_id)
        """)
        
        # Create index on created_at for sorting
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_evaluations_created_at 
            ON evaluations(created_at DESC)
        """)
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def save_evaluation(
    session_id: str,
    flow: str,
    facts: Dict[str, Any],
    stats: Dict[str, Any],
    evaluation: Dict[str, Any],
    assumptions: Dict[str, Any] = None
) -> str:
    """Save a property evaluation to the database."""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        eval_id = str(uuid.uuid4())
        
        cur.execute("""
            INSERT INTO evaluations 
            (id, session_id, flow, address, property_data, market_stats, evaluation_data, assumptions)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            eval_id,
            session_id,
            flow,
            facts.get('address', 'Unknown'),
            json.dumps(facts),
            json.dumps(stats),
            json.dumps(evaluation),
            json.dumps(assumptions or {})
        ))
        
        result = cur.fetchone()
        conn.commit()
        
        return result[0] if result else eval_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_evaluations_by_session(session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve all evaluations for a session."""
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, flow, address, property_data, market_stats, 
                   evaluation_data, assumptions, created_at
            FROM evaluations
            WHERE session_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (session_id, limit))
        
        rows = cur.fetchall()
        
        # Convert to list of dicts
        evaluations = []
        for row in rows:
            evaluations.append({
                'id': str(row['id']),
                'flow': row['flow'],
                'address': row['address'],
                'property_data': row['property_data'],
                'market_stats': row['market_stats'],
                'evaluation_data': row['evaluation_data'],
                'assumptions': row['assumptions'],
                'created_at': row['created_at'].isoformat()
            })
        
        return evaluations
        
    finally:
        cur.close()
        conn.close()


def get_evaluation_by_id(eval_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a specific evaluation by ID."""
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT id, session_id, flow, address, property_data, market_stats, 
                   evaluation_data, assumptions, created_at
            FROM evaluations
            WHERE id = %s
        """, (eval_id,))
        
        row = cur.fetchone()
        
        if not row:
            return None
        
        return {
            'id': str(row['id']),
            'session_id': row['session_id'],
            'flow': row['flow'],
            'address': row['address'],
            'property_data': row['property_data'],
            'market_stats': row['market_stats'],
            'evaluation_data': row['evaluation_data'],
            'assumptions': row['assumptions'],
            'created_at': row['created_at'].isoformat()
        }
        
    finally:
        cur.close()
        conn.close()


def delete_evaluation(eval_id: str, session_id: str) -> bool:
    """Delete an evaluation (only if it belongs to the session)."""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            DELETE FROM evaluations
            WHERE id = %s AND session_id = %s
        """, (eval_id, session_id))
        
        deleted = cur.rowcount > 0
        conn.commit()
        
        return deleted
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()
