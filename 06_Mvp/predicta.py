"""Predicta - punto de entrada del MVP.

    python3.11 06_Mvp/predicta.py ingesta   # pipeline + motor
    python3.11 06_Mvp/predicta.py api       # servidor FastAPI
"""
from pathlib import Path
import json
import os
import sys

RAIZ = Path(__file__).resolve().parents[1]


def main():
    orden = sys.argv[1] if len(sys.argv) > 1 else "ingesta"
    if orden == "ingesta":
        from ingesta import ejecutar

        print(json.dumps(ejecutar(), ensure_ascii=False))
    elif orden == "api":
        import uvicorn
        from api import app

        uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PORT", "8000")))
    else:
        print("Uso: predicta.py [ingesta|api]")
        raise SystemExit(2)


if __name__ == "__main__":
    main()
