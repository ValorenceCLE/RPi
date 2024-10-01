import asyncio
import aiofiles #type: ignore
import json
import os
from influxdb_client import InfluxDBClient #type: ignore
from influxdb_client.rest import ApiException #type: ignore

# I have no idea how this code works, but it does.
# PROCEED WITH CAUTION IF YOU PLAN TO MODIFY THIS SCRIPT
# InfluxDB has terrible documetnation for this.
# Hours Wasted: 18
# Suicidal thoughts due to this script: 4

# We may be able to refactor this whole script using these functions
# => from influxdb_client.domain import Dashboard, DashboardWithViewProperties

class Dashboard_Setup:
    def __init__(self):
        self.token = os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN')
        self.org = os.getenv('DOCKER_INFLUXDB_INIT_ORG')
        self.bucket = os.getenv('DOCKER_INFLUXDB_INIT_BUCKET')
        self.url = os.getenv('INFLUXDB_URL')
        self.dashboard_file = "system_performance.json"
        self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
        self.dashboard_id = None

    def get_org_id(self):
        try:
            orgs = self.client.organizations_api().find_organizations()
            for org in orgs:
                if org.name == self.org:
                    return org.id
        except Exception as e:
            print(f"Error getting organization ID: {e}")
        return None

    async def check_existing_dashboard(self):
        try:
            dashboards = self.client.api_client.call_api(
                resource_path="/api/v2/dashboards",
                method='GET',
                header_params={
                    "Authorization": f"Token {self.token}",
                    "Accept": "application/json"
                },
                response_type='object'
            )

            if dashboards[1] == 200:
                dashboard_list = dashboards[0].get('dashboards', [])
                if dashboard_list:
                    print("Dashboard(s) already exist. Skipping creation.")
                    return True
            else:
                print(f"Failed to retrieve dashboards: {dashboards[1]} - {dashboards[0]}")
                return False

        except ApiException as e:
            print(f"Error during API request: {e.status} - {e.body}")
            return False

    async def create_dashboard(self):
        if await self.check_existing_dashboard():
            return  # Skip creation if a dashboard already exists

        async with aiofiles.open(self.dashboard_file, 'r') as file:
            dashboard_data = await file.read()
            dashboard_data = json.loads(dashboard_data)

        cells = []
        if "included" in dashboard_data["content"]:
            for item in dashboard_data["content"]["included"]:
                if item["type"] == "cell":
                    cells.append({
                        "x": item["attributes"]["x"],
                        "y": item["attributes"]["y"],
                        "w": item["attributes"]["w"],
                        "h": item["attributes"]["h"],
                    })

        dashboard_payload = {
            "name": "System Performance",
            "description": "System Overview",
            "orgID": self.get_org_id(),
            "cells": cells
        }

        try:
            response = self.client.api_client.call_api(
                resource_path="/api/v2/dashboards",
                method='POST',
                header_params={
                    "Authorization": f"Token {self.token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                body=dashboard_payload,
                response_type='object'
            )

            if response[1] == 201:
                print("Dashboard created successfully!")
                self.dashboard_id = response[0]['id']
                print(f"Dashboard ID: {self.dashboard_id}")
            else:
                print(f"Failed to create dashboard: {response[1]} - {response[0]}")
                print(f"Response body: {response[0]}")

        except ApiException as e:
            print(f"Error during API request: {e.status} - {e.body}")
        except Exception as e:
            print(f"Error during API request: {e}")

    async def get_cells(self):
        try:
            response = self.client.api_client.call_api(
                resource_path=f"/api/v2/dashboards/{self.dashboard_id}",
                method='GET',
                header_params={
                    "Authorization": f"Token {self.token}",
                    "Accept": "application/json"
                },
                response_type='object'
            )

            if response[1] == 200:
                return response[0]['cells']
            else:
                print(f"Failed to retrieve cells: {response[1]} - {response[0]}")
                return []

        except ApiException as e:
            print(f"Error during API request: {e.status} - {e.body}")
            return []

    async def update_cells(self, cells_from_json, cell_ids):
        for i, cell in enumerate(cell_ids):
            try:
                view_data = cells_from_json[i].get("attributes", {})
                properties = view_data.get("properties", {})

                if not properties:
                    print(f"Skipping update for cell {cell['id']} due to missing properties.")
                    continue

                update_payload = {
                    "name": view_data.get("name", ""),
                    "properties": {
                        "axes": properties.get("axes", {}),
                        "colors": properties.get("colors", []),
                        "decimalPlaces": properties.get("decimalPlaces", {}),
                        "generateXAxisTicks": properties.get("generateXAxisTicks", []),
                        "generateYAxisTicks": properties.get("generateYAxisTicks", []),
                        "hoverDimension": properties.get("hoverDimension", "auto"),
                        "legend": properties.get("legend", {}),
                        "legendColorizeRows": properties.get("legendColorizeRows", True),
                        "legendOpacity": properties.get("legendOpacity", 0.1),
                        "legendOrientationThreshold": properties.get("legendOrientationThreshold", 0),
                        "note": properties.get("note", ""),
                        "position": properties.get("position", "overlaid"),
                        "prefix": properties.get("prefix", ""),
                        "queries": properties.get("queries", []),
                        "shadeBelow": properties.get("shadeBelow", True),
                        "shape": properties.get("shape", "chronograf-v2"),
                        "showNoteWhenEmpty": properties.get("showNoteWhenEmpty", True),
                        "suffix": properties.get("suffix", ""),
                        "timeFormat": properties.get("timeFormat", ""),
                        "type": properties.get("type", "line-plus-single-stat"),
                        "xColumn": properties.get("xColumn", "string"),
                        "xTickStart": properties.get("xTickStart", 0.1),
                        "xTickStep": properties.get("xTickStep", 0.1),
                        "xTotalTicks": properties.get("xTotalTicks", 0),
                        "yColumn": properties.get("yColumn", "string"),
                        "yTickStart": properties.get("yTickStart", 0.1),
                        "yTickStep": properties.get("yTickStep", 0.1),
                        "yTotalTicks": properties.get("yTotalTicks", 0)
                    }
                }

                response = self.client.api_client.call_api(
                    resource_path=f"/api/v2/dashboards/{self.dashboard_id}/cells/{cell['id']}/view",
                    method='PATCH',
                    header_params={
                        "Authorization": f"Token {self.token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body=update_payload,
                    response_type='object'
                )

                if response[1] == 200:
                    print(f"Cell {cell['id']} updated successfully!")
                else:
                    print(f"Failed to update cell {cell['id']}: {response[1]} - {response[0]}")

            except KeyError as e:
                print(f"KeyError during update for cell {cell['id']}: {e}")
            except ApiException as e:
                print(f"Error during API request for cell {cell['id']}: {e.status} - {e.body}")
            except Exception as e:
                print(f"Error during API request for cell {cell['id']}: {e}")

    async def run(self):
        await self.create_dashboard()
        if self.dashboard_id:  # Only proceed if a new dashboard was created
            cell_ids = await self.get_cells()

            async with aiofiles.open(self.dashboard_file, 'r') as file:
                dashboard_data = await file.read()
                dashboard_data = json.loads(dashboard_data)

            cells_from_json = [item for item in dashboard_data["content"]["included"] if item["type"] == "view"]

            await self.update_cells(cells_from_json, cell_ids)

    def close(self):
        self.client.close()


if __name__ == "__main__":
    dashboard = Dashboard_Setup()
    asyncio.run(dashboard.run())
    dashboard.close()
