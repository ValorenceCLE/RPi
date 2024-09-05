from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync # type: ignore
from influxdb_client.client.query_api_async import QueryApiAsync # type: ignore
from fastapi import APIRouter, HTTPException, Query # type: ignore
from typing import List, Optional
import os

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
            # Execute the query and get the result
            result = await self.query_api.query(query, org=self.org)
            alerts = []
            
            # Iterate through the tables in the result
            for table in result:
                for record in table.records:
                    alerts.append({
                        "timestamp": record.values.get("_time"),  # Access time using get_time()
                        "source": record.values.get("source"),  # Source is a tag
                        "level": record.values.get("level"),  # Level is a tag
                        "value": record.values.get("_value") # Access the actual value using get_value()
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
        raise HTTPException(status_code=500, detail=f"Error Fetching Alerts: {e}")