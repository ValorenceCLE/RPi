from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client.client.query_api_async import QueryApiAsync
from fastapi import APIRouter, HTTPException
from typing import Dict, List
from core.config import settings

router = APIRouter()

class WebGrapher:
    def __init__(self):
        self.token = settings.TOKEN
        self.org = settings.ORG
        self.bucket = settings.BUCKET
        self.url = settings.INFLUXDB_URL
        self.client = None
        self.query_api = None
    
    async def __aenter__(self):
        await self.initialize_client()
        return self
    async def __aexit__(self, exc_type,exc,tb):
        await self.client.close()
        
    async def initialize_client(self):
        self.client = InfluxDBClientAsync(url=self.url, token=self.token, org=self.org)
        self.query_api = QueryApiAsync(self.client)
        
    async def base_results(self, page_name: str, time_frame: str) -> List[Dict]:
        query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -{time_frame})
                |> filter(fn: (r) => r._measurement == "{page_name}")
        '''
        try:
            results = await self.query_api.query(query, org=self.org)
            aggregated = {}
            for table in results:
                for record in table.records:
                    ts = record.get_time()
                    if ts not in aggregated:
                        aggregated[ts] = {}
                    field = record.get_field()
                    value = record.get_value()
                    aggregated[ts][field] = value
            sorted_data = sorted(
                [{"timestamp": ts, **fields} for ts, fields in aggregated.items()],
                key=lambda x: x["timestamp"]
            )
            return {
                "measurement": page_name,
                "data": sorted_data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching data: {e}")

@router.get("/{page_name}/demo/{time_frame}")
async def get_graph_data(page_name: str, time_frame: str):
    stream_map = settings.STREAM_MAP
    stream_name = stream_map.get(page_name)
    async with WebGrapher() as grapher:
        data = await grapher.base_results(stream_name, time_frame)
        return data
            
