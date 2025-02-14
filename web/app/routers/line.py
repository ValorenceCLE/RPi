
#! -----REFACTORING NOTES-----
#? This file is mostly good, minor changes to work with Vue

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
        
    def generate_query(self, page_name: str, timeframe: str) -> str:
        if timeframe == '1h':
            aggregation = None
        elif timeframe == '3h':
            aggregation = '1m'
        elif timeframe == '6h':
            aggregation = '2m'
        elif timeframe == '12h':
            aggregation = '4m'
        elif timeframe == '1d':
            aggregation = '8m'
        elif timeframe == '2d':
            aggregation = '16m'
            
        base_query = f"""
        from(bucket: "{self.bucket}")
            |> range(start: -{timeframe})
            |> filter(fn: (r) => r._measurement == "{page_name}")
        """
        if aggregation:
            base_query += f"""
            |> aggregateWindow(every: {aggregation}, fn: mean, createEmpty: false)
            """        
        return base_query
    
    async def base_results(self, page_name: str, time_frame: str) -> List[Dict]:
        try:
            results = await self.query_api.query(self.generate_query(page_name, time_frame), org=self.org)
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

@router.get("/{page_name}/data/{time_frame}")
async def get_graph_data(page_name: str, time_frame: str):
    stream_map = settings.STREAM_MAP
    stream_name = stream_map.get(page_name)
    async with WebGrapher() as grapher:
        data = await grapher.base_results(stream_name, time_frame)
        return data
            
