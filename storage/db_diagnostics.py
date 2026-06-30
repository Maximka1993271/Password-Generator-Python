"""
Database diagnostics and auto-repair module.
Диагностика базы данных и автоматическое восстановление.
Діагностика бази даних та автоматичне відновлення.
"""
from __future__ import annotations
import os
import sqlite3
import json
import shutil
from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime

from utils.logger import get_logger
from utils.logging_ext import log_operation, log_error_with_context
from storage.database_queries import get_db_path, _db_lock
from storage.database_health import DatabaseHealthCheck, DatabaseRecovery

logger = get_logger("db_diagnostics")

# Diagnostic results
DIAGNOSTIC_OK = "ok"
DIAGNOSTIC_WARNING = "warning"
DIAGNOSTIC_ERROR = "error"
DIAGNOSTIC_CRITICAL = "critical"


class DatabaseDiagnostics:
    """
    Database diagnostics and auto-repair.
    Диагностика базы данных и автоматическое восстановление.
    Діагностика бази даних та автоматичне відновлення.
    """
    
    _instance = None
    
    def __new__(cls):
        """
        Handle new.
        Обработать new.
        Обробити new.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._diagnostic_log = []
        return cls._instance
    
    def run_diagnostics(self, auto_repair: bool = True) -> Dict[str, Any]:
        """
        Run full database diagnostics.
        
        Args:
            auto_repair: Whether to attempt auto-repair
        
        Returns:
            Diagnostic results dictionary
        """
        db_path = get_db_path()
        
        with log_operation("Database diagnostics"):
            results = {
                "status": DIAGNOSTIC_OK,
                "timestamp": datetime.now().isoformat(),
                "db_path": db_path,
                "db_exists": False,
                "db_size": 0,
                "db_size_mb": 0,
                "checks": [],
                "repairs": [],
                "errors": [],
                "recommendations": []
            }
            
            # Check if DB exists
            if not os.path.exists(db_path):
                results["status"] = DIAGNOSTIC_CRITICAL
                results["db_exists"] = False
                results["errors"].append("Database file does not exist")
                results["recommendations"].append("Create new database or restore from backup")
                self._log_diagnostic("DB_NOT_EXISTS", "critical", "Database file not found")
                return results
            
            results["db_exists"] = True
            
            # Get DB size
            try:
                size = os.path.getsize(db_path)
                results["db_size"] = size
                results["db_size_mb"] = round(size / (1024 * 1024), 2)
            except (OSError, IOError, PermissionError) as e:
                results["errors"].append(f"Failed to get DB size: {e}")
            
            # Run integrity check
            integrity = DatabaseHealthCheck.check_integrity(db_path)
            results["checks"].append({
                "name": "integrity_check",
                "status": integrity.get("status", DIAGNOSTIC_ERROR),
                "message": integrity.get("message", "")
            })
            
            if integrity.get("status") != "ok":
                results["status"] = DIAGNOSTIC_ERROR
                self._log_diagnostic("INTEGRITY_FAIL", "error", integrity.get("message", ""))
                
                if auto_repair:
                    repair_result = self._attempt_repair(db_path)
                    results["repairs"].append(repair_result)
                    
                    if repair_result.get("success"):
                        results["status"] = DIAGNOSTIC_WARNING
                        results["recommendations"].append("Database repaired, verify data integrity")
                    else:
                        results["status"] = DIAGNOSTIC_CRITICAL
                        results["recommendations"].append("Database repair failed, restore from backup")
                        results["recommendations"].append("Or create new database and re-import passwords")
            
            # Check for corruption
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA quick_check")
                quick_result = cursor.fetchone()
                conn.close()
                
                if quick_result and quick_result[0] != "ok":
                    results["checks"].append({
                        "name": "quick_check",
                        "status": DIAGNOSTIC_ERROR,
                        "message": quick_result[0]
                    })
                    results["status"] = DIAGNOSTIC_ERROR
                    self._log_diagnostic("QUICK_CHECK_FAIL", "error", quick_result[0])
                else:
                    results["checks"].append({
                        "name": "quick_check",
                        "status": DIAGNOSTIC_OK,
                        "message": "OK"
                    })
            except sqlite3.Error as e:
                results["errors"].append(f"Quick check error: {e}")
            
            # Check table integrity
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                table_count = len(tables)
                if table_count == 0:
                    results["checks"].append({
                        "name": "table_check",
                        "status": DIAGNOSTIC_CRITICAL,
                        "message": "No tables found"
                    })
                    results["status"] = DIAGNOSTIC_CRITICAL
                    self._log_diagnostic("NO_TABLES", "critical", "Database has no tables")
                else:
                    results["checks"].append({
                        "name": "table_check",
                        "status": DIAGNOSTIC_OK,
                        "message": f"{table_count} tables found"
                    })
            except sqlite3.Error as e:
                results["errors"].append(f"Table check error: {e}")
            
            # Check backup availability
            from storage.database_backup import get_backup_manager
            backup_mgr = get_backup_manager()
            backup_count = backup_mgr.get_backup_count()
            
            if backup_count == 0:
                results["checks"].append({
                    "name": "backup_check",
                    "status": DIAGNOSTIC_WARNING,
                    "message": "No backups found"
                })
                results["recommendations"].append("Create database backup")
            else:
                results["checks"].append({
                    "name": "backup_check",
                    "status": DIAGNOSTIC_OK,
                    "message": f"{backup_count} backups available"
                })
            
            # Final status
            if results["status"] == DIAGNOSTIC_CRITICAL:
                logger.critical(f"Database diagnostics CRITICAL: {results['errors']}")
            elif results["status"] == DIAGNOSTIC_ERROR:
                logger.error(f"Database diagnostics ERROR: {results['errors']}")
            elif results["status"] == DIAGNOSTIC_WARNING:
                logger.warning(f"Database diagnostics WARNING: {results['recommendations']}")
            else:
                logger.info("Database diagnostics OK")
            
            return results
    
    def _attempt_repair(self, db_path: str) -> Dict[str, Any]:
        """
        Attempt to repair database.
        
        Args:
            db_path: Path to database
        
        Returns:
            Repair result dictionary
        """
        result = {
            "success": False,
            "attempted": False,
            "message": "",
            "backup_created": False,
            "backup_path": None
        }
        
        with log_operation("Database repair attempt"):
            try:
                # Create backup before repair
                from storage.database_backup import create_database_backup
                backup_path = create_database_backup()
                if backup_path:
                    result["backup_created"] = True
                    result["backup_path"] = backup_path
                
                result["attempted"] = True
                
                # Attempt repair
                success = DatabaseRecovery.attempt_repair(db_path)
                result["success"] = success
                
                if success:
                    result["message"] = "Database repaired successfully"
                    logger.info("Database repaired successfully")
                    
                    # Verify repair
                    integrity = DatabaseHealthCheck.check_integrity(db_path)
                    if integrity.get("status") != "ok":
                        result["success"] = False
                        result["message"] = f"Repair failed verification: {integrity.get('message')}"
                else:
                    result["message"] = "Repair attempt failed"
                    logger.warning("Database repair attempt failed")
                    
            except (OSError, ValueError, TypeError, AttributeError, RuntimeError) as e:
                result["message"] = f"Repair error: {e}"
                log_error_with_context(e, "Database repair error")
            
            return result
    
    def _log_diagnostic(self, code: str, level: str, message: str) -> None:
        """Log diagnostic event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "code": code,
            "level": level,
            "message": message
        }
        self._diagnostic_log.append(entry)
        
        # Keep last 100 entries
        if len(self._diagnostic_log) > 100:
            self._diagnostic_log = self._diagnostic_log[-100:]
    
    def get_diagnostic_log(self) -> List[Dict[str, Any]]:
        """Get diagnostic log."""
        return self._diagnostic_log.copy()
    
    def clear_diagnostic_log(self) -> None:
        """Clear diagnostic log."""
        self._diagnostic_log = []
    
    def quick_check(self) -> Tuple[bool, str]:
        """
        Quick database health check.
        
        Returns:
            (is_healthy, message)
        """
        db_path = get_db_path()
        return DatabaseHealthCheck.quick_health_check(db_path)
    
    def create_backup(self) -> Optional[str]:
        """Create database backup."""
        from storage.database_backup import create_database_backup
        return create_database_backup()
    
    def restore_latest_backup(self) -> bool:
        """Restore latest backup."""
        from storage.database_backup import restore_database_from_backup
        return restore_database_from_backup()
    
    def get_backup_info(self) -> Dict[str, Any]:
        """Get backup information."""
        from storage.database_backup import get_backup_manager
        mgr = get_backup_manager()
        
        backups = mgr.get_backups()
        
        return {
            "count": len(backups),
            "latest": backups[0].to_dict() if backups else None,
            "oldest": backups[-1].to_dict() if backups else None,
            "total_size": sum(b.size for b in backups) if backups else 0
        }


def run_database_diagnostics(auto_repair: bool = True) -> Dict[str, Any]:
    """
    Convenience function to run database diagnostics.
    
    Args:
        auto_repair: Whether to attempt auto-repair
    
    Returns:
        Diagnostic results
    """
    diag = DatabaseDiagnostics()
    return diag.run_diagnostics(auto_repair)


def quick_database_check() -> Tuple[bool, str]:
    """
    Quick database health check.
    
    Returns:
        (is_healthy, message)
    """
    diag = DatabaseDiagnostics()
    return diag.quick_check()


__all__ = [
    'DatabaseDiagnostics',
    'run_database_diagnostics',
    'quick_database_check',
    'DIAGNOSTIC_OK',
    'DIAGNOSTIC_WARNING',
    'DIAGNOSTIC_ERROR',
    'DIAGNOSTIC_CRITICAL',
]