"""
Superset 配置：允许在外部 iframe 中安全嵌入
"""
import os
import sys
import uuid
import logging
from typing import List

# Force unbuffered
sys.stdout.reconfigure(line_buffering=True) if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(line_buffering=True) if hasattr(sys.stderr, 'reconfigure') else None

def debug_log(msg):
    # Write to both stdout and stderr to be safe
    try:
        print(f"[UUID_PATCH_v8] {msg}", file=sys.stdout, flush=True)
        print(f"[UUID_PATCH_v8] {msg}", file=sys.stderr, flush=True)
    except:
        pass

debug_log(">>>>>>>>>> SUPERSET CONFIG LOADING (v8) <<<<<<<<<<")

# =================================================================
# MONKEY PATCH
# =================================================================
try:
    from sqlalchemy_utils.types import uuid as uuid_module
    debug_log("Applying UUID monkey patch...")

    original_coerce = uuid_module.UUIDType._coerce

    @staticmethod
    def patched_coerce(value):
        if value and not isinstance(value, uuid.UUID):
            # Attempt to handle string-as-bytes (common in SQLite/drivers)
            if isinstance(value, (bytes, bytearray)):
                if len(value) > 16:
                    # Try decoding as utf-8/ascii if it looks like a string UUID
                    try:
                        decoded = value.decode('utf-8').strip().strip('"').strip("'")
                        return uuid.UUID(decoded)
                    except:
                        pass
                    try:
                        decoded = value.decode('ascii').strip().strip('"').strip("'")
                        return uuid.UUID(decoded)
                    except:
                        pass
            
            try:
                value = uuid.UUID(value)
            except (TypeError, ValueError):
                try:
                    value = uuid.UUID(bytes=value)
                except Exception as e:
                    # FATAL ERROR: Capture details in the exception message itself
                    # so it appears in the traceback even if logs are suppressed
                    error_msg = f"FATAL_UUID_ERROR: value_type={type(value)}, value_repr={value!r}"
                    if isinstance(value, (bytes, bytearray)):
                        error_msg += f", len={len(value)}, hex={value.hex()}"
                    
                    debug_log(error_msg)
                    logging.error(error_msg)
                    
                    # Raise a new error with the debug info
                    raise ValueError(error_msg) from e
        
        return value

    uuid_module.UUIDType._coerce = patched_coerce
    debug_log("UUID monkey patch applied successfully!")

except Exception as e:
    debug_log(f"FATAL: Failed to apply patch: {e}")
    import traceback
    traceback.print_exc()

# =================================================================

def _load_parent_origins() -> List[str]:
    raw = os.getenv(
        "SUPERSET_PARENT_ORIGINS",
        "http://localhost:3000 http://127.0.0.1:3000",
    )
    tokens = raw.replace(",", " ").split()
    origins = [token.strip() for token in tokens if token.strip()]
    if not origins:
        origins.append("'self'")
    return origins


_FRAME_ANCESTORS = " ".join(_load_parent_origins())

ENABLE_EMBEDDED_SUPERSET = True
EMBEDDED_SUPERSET_TIMEOUT = 3600
EMBEDDED_SUPERSET_KEY = os.getenv("SUPERSET_EMBED_SECRET", "superset-embed-secret")
FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}
GUEST_ROLE_NAME = os.getenv("SUPERSET_GUEST_ROLE", "Gamma")
PUBLIC_ROLE_LIKE_GAMMA = True

HTTP_HEADERS = {
    "X-Frame-Options": "ALLOWALL",
    "Content-Security-Policy": f"frame-ancestors {_FRAME_ANCESTORS}",
}

OVERRIDE_HTTP_HEADERS = HTTP_HEADERS
TALISMAN_ENABLED = False
TALISMAN_CONFIG = {}
