from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync  # type: ignore
from influxdb_client.client.query_api_async import QueryApiAsync  # type: ignore
from fastapi import APIRouter, HTTPException, Query  # type: ignore
from typing import List, Optional
import os
from datetime import datetime

router = APIRouter()

class InfluxService:
    def __init__(self):
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.client = InfluxDBClientAsync(url=self.url, token=self.token, org=self.org)
        self.query_api = QueryApiAsync(self.client)

    async def fetch_alerts(self, limit: int, offset: int) -> List[dict]:
        query = f'from(bucket: "{self.bucket}") |> range(start: 0) |> filter(fn: (r) => r._measurement == "alerts") |> sort(columns: ["_time"], desc: true) |> limit(n: {limit + 1}, offset: {offset})'
        try:
            result = await self.query_api.query(query, org=self.org)
            alerts = []
            for table in result:
                for record in table.records:
                    alerts.append({
                        "timestamp": record.values.get("_time"),
                        "source": record.values.get("source"),
                        "level": record.values.get("level"),
                        "value": record.values.get("_value")
                    })
            has_more = len(alerts) > limit
            return alerts[:limit], has_more
        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return [], False

    # New Search Function to dynamically build the query
    async def search_alerts(self, limit: int, offset: int, start: Optional[str] = None, end: Optional[str] = None, level: Optional[str] = None, source: Optional[str] = None) -> List[dict]:
        query = f'from(bucket: "{self.bucket}")'

        # Only add the range filter if start and/or end is provided
        if start and end:
            start_iso = datetime.strptime(start, "%Y-%m-%d").isoformat() + "Z"
            end_iso = datetime.strptime(end, "%Y-%m-%d").isoformat() + "Z"
            query += f' |> range(start: {start_iso}, stop: {end_iso})'
        else:
            # If no time frame is given, select a broad range (you may change this as per your data structure)
            query += ' |> range(start: 1970-01-01T00:00:00Z, stop: now())'

        # Add the measurement filter
        query += ' |> filter(fn: (r) => r._measurement == "alerts")'

        # Apply filters for level and source if provided
        if level:
            query += f' |> filter(fn: (r) => r.level == "{level}")'
        if source:
            query += f' |> filter(fn: (r) => r.source == "{source}")'

        # Sort and limit the results
        query += f' |> sort(columns: ["_time"], desc: true) |> limit(n: {limit + 1}, offset: {offset})'

        try:
            result = await self.query_api.query(query, org=self.org)
            alerts = []
            for table in result:
                for record in table.records:
                    alerts.append({
                        "timestamp": record.values.get("_time"),
                        "source": record.values.get("source"),
                        "level": record.values.get("level"),
                        "value": record.values.get("_value")
                    })
            has_more = len(alerts) > limit
            return alerts[:limit], has_more
        except Exception as e:
            print(f"Error fetching alerts: {e}")
            return [], False

influx_service = InfluxService()

@router.get("/api/alerts")
async def get_alerts(limit: int = Query(10, gt=0), offset: int = Query(0, ge=0)):
    try:
        alerts, has_more = await influx_service.fetch_alerts(limit=limit, offset=offset)
        if not alerts:
            return {"message": "No alerts available", "has_more": False}
        return {"alerts": alerts, "has_more": has_more}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {e}")

@router.get("/api/search_alerts")
async def search_alerts(
    limit: int = Query(10, gt=0),
    offset: int = Query(0, ge=0),
    start: Optional[str] = Query(None),
    end: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    level: Optional[str] = Query(None)
):
    try:
        alerts, has_more = await influx_service.search_alerts(
            limit=limit,
            offset=offset,
            start=start,
            end=end,
            source=source,
            level=level
        )
        if not alerts:
            return {"message": "No alerts available", "has_more": False}
        return {"alerts": alerts, "has_more": has_more}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error Fetching Alerts: {e}")