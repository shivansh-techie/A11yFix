import io
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from app.ai_fix import get_fix
from app.database import create_db, engine, get_session
from app.models import Scan, Violation
from app.scanner import scan_url
from app.scoring import compute_score


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db()
    yield


app = FastAPI(title="A11yFix API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# runs in thread pool (FastAPI handles sync bg tasks that way)
def _do_scan(scan_id: int, url: str):
    from sqlmodel import Session as S

    with S(engine) as db:
        scan = db.get(Scan, scan_id)
        scan.status = "running"
        db.add(scan)
        db.commit()

        try:
            result = scan_url(url)
            violations = result["violations"]
            score = compute_score(violations)

            # deduplicate: only call the fix function once per unique rule
            fix_cache = {}
            for v in violations:
                rid = v["rule_id"]
                if rid not in fix_cache:
                    try:
                        fix_cache[rid] = get_fix(rid, v["description"], v["html"], v["wcag_tags"])
                    except Exception:
                        fix_cache[rid] = {"fixed_html": v["html"], "explanation": "Fix unavailable."}

                fix = fix_cache[rid]
                db.add(Violation(
                    scan_id=scan_id,
                    rule_id=rid,
                    impact=v["impact"],
                    description=v["description"],
                    target=v["target"],
                    html_snippet=v["html"],
                    wcag_tags=", ".join(v["wcag_tags"]),
                    fix_snippet=fix.get("fixed_html"),
                    fix_explanation=fix.get("explanation"),
                ))

            scan.score = score
            scan.violation_count = len(violations)
            scan.status = "completed"

        except Exception as e:
            scan.status = "failed"
            scan.error_message = str(e)
            print(f"[scan {scan_id}] failed: {e}")

        db.add(scan)
        db.commit()


class ScanRequest(BaseModel):
    url: str


@app.post("/api/scans", status_code=202)
def create_scan(req: ScanRequest, bg: BackgroundTasks, db: Session = Depends(get_session)):
    scan = Scan(url=req.url)
    db.add(scan)
    db.commit()
    db.refresh(scan)
    bg.add_task(_do_scan, scan.id, req.url)
    return {"scan_id": scan.id, "status": "pending"}


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: int, db: Session = Depends(get_session)):
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(404, "not found")

    violations = db.exec(select(Violation).where(Violation.scan_id == scan_id)).all()

    return {
        "id": scan.id,
        "url": scan.url,
        "timestamp": scan.timestamp,
        "score": scan.score,
        "violation_count": scan.violation_count,
        "status": scan.status,
        "error_message": scan.error_message,
        "violations": [
            {
                "rule_id": v.rule_id,
                "impact": v.impact,
                "description": v.description,
                "target": v.target,
                "html_snippet": v.html_snippet,
                "wcag_tags": v.wcag_tags,
                "fix_snippet": v.fix_snippet,
                "fix_explanation": v.fix_explanation,
            }
            for v in violations
        ],
    }


@app.get("/api/scans")
def list_scans(db: Session = Depends(get_session)):
    scans = db.exec(select(Scan).order_by(Scan.timestamp.desc()).limit(50)).all()
    return [
        {
            "id": s.id,
            "url": s.url,
            "timestamp": s.timestamp,
            "score": s.score,
            "violation_count": s.violation_count,
            "status": s.status,
        }
        for s in scans
    ]


@app.get("/api/scans/{scan_id}/pdf")
def export_pdf(scan_id: int, db: Session = Depends(get_session)):
    from jinja2 import Environment, FileSystemLoader
    from weasyprint import HTML

    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(404, "not found")
    if scan.status != "completed":
        raise HTTPException(400, "scan not finished yet")

    violations = db.exec(select(Violation).where(Violation.scan_id == scan_id)).all()

    templates_dir = Path(__file__).parent.parent / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_dir)))
    html_str = env.get_template("report.html").render(scan=scan, violations=violations)

    try:
        pdf = HTML(string=html_str).write_pdf()
    except Exception as e:
        raise HTTPException(500, f"PDF generation failed: {e}")

    return StreamingResponse(
        io.BytesIO(pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="a11yfix-{scan_id}.pdf"'},
    )


@app.get("/health")
def health():
    return {"status": "ok"}
