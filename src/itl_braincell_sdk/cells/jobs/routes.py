"""Jobs routes — Weaviate-only, no PostgreSQL entities."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from itl_braincell_sdk.cells.jobs.schema import BatchJobInput, JobInput, JobSearchQuery, SearchResult
from itl_braincell_sdk.core.database import get_db
from itl_braincell_sdk.services.weaviate_service import get_weaviate_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def store_job(job: JobInput, db: Session = Depends(get_db)):
    try:
        weaviate = get_weaviate_service()
        success = weaviate.index_job(
            job_id=job.job_id,
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            url=job.url,
            source=job.source,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            job_type=job.job_type,
            seniority_level=job.seniority_level,
            posted_date=job.posted_date,
            tags=job.tags,
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store job")
        return {"status": "success", "message": f"Job stored: {job.job_id}", "job_id": job.job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error storing job: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def store_jobs_batch(batch: BatchJobInput, db: Session = Depends(get_db)):
    weaviate = get_weaviate_service()
    successful, failed, errors = 0, 0, []

    for job in batch.jobs:
        try:
            ok = weaviate.index_job(
                job_id=job.job_id,
                title=job.title,
                company=job.company,
                location=job.location,
                description=job.description,
                url=job.url,
                source=job.source,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                job_type=job.job_type,
                seniority_level=job.seniority_level,
                posted_date=job.posted_date,
                tags=job.tags,
            )
            if ok:
                successful += 1
            else:
                failed += 1
                errors.append(f"Failed to store job: {job.job_id}")
        except Exception as e:
            failed += 1
            errors.append(f"Error storing {job.job_id}: {e}")

    return {
        "status": "success",
        "successful": successful,
        "failed": failed,
        "total": len(batch.jobs),
        "errors": errors,
    }


@router.post("/search", response_model=list[SearchResult])
async def search_jobs(search_query: JobSearchQuery, db: Session = Depends(get_db)):
    try:
        weaviate = get_weaviate_service()
        results = weaviate.search_jobs(
            query=search_query.query,
            limit=search_query.limit,
            source=search_query.source,
            job_type=search_query.job_type,
            location=search_query.location,
        )
        return [
            SearchResult(
                id=UUID(r.get("job_id", r.get("uuid", ""))),
                type="job",
                title=r.get("title", ""),
                content=r.get("description", ""),
                similarity_score=1 - r.get("_additional", {}).get("distance", 1),
                metadata={
                    "company": r.get("company", ""),
                    "location": r.get("location", ""),
                    "source": r.get("source", ""),
                    "job_type": r.get("job_type", ""),
                    "salary_min": r.get("salary_min"),
                    "salary_max": r.get("salary_max"),
                    "url": r.get("url", ""),
                    "posted_date": r.get("posted_date", ""),
                },
            )
            for r in results
            if r.get("job_id") or r.get("uuid")
        ]
    except Exception as e:
        logger.error("Error searching jobs: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    try:
        weaviate = get_weaviate_service()
        results = weaviate.search_jobs(query=f"job id {job_id}", limit=1)
        if not results:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return {"status": "success", "job": results[0]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving job %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    try:
        weaviate = get_weaviate_service()
        if not weaviate.delete_job(job_id):
            raise HTTPException(status_code=500, detail="Failed to delete job")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting job %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{job_id}")
async def update_job(job_id: str, updates: dict, db: Session = Depends(get_db)):
    try:
        weaviate = get_weaviate_service()
        weaviate.delete_job(job_id)
        success = weaviate.index_job(
            job_id=updates.get("job_id", job_id),
            title=updates.get("title", ""),
            company=updates.get("company", ""),
            location=updates.get("location", ""),
            description=updates.get("description", ""),
            url=updates.get("url", ""),
            source=updates.get("source", ""),
            salary_min=updates.get("salary_min"),
            salary_max=updates.get("salary_max"),
            job_type=updates.get("job_type"),
            seniority_level=updates.get("seniority_level"),
            posted_date=updates.get("posted_date"),
            tags=updates.get("tags"),
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update job")
        return {"status": "success", "message": f"Job updated: {job_id}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating job %s: %s", job_id, e)
        raise HTTPException(status_code=500, detail=str(e))
