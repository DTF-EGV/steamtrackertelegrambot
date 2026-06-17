import httpx
from typing import Optional

class SteamService:
    def __init__(self):
        self.base_url = "https://store.steampowered.com/api/appdetails"

    async def get_game_details(self, app_id: int) -> Optional[dict]:
        params = {
            "appids": app_id,
            "cc": "ru",
            "l": "russian"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params)
                if response.status_code != 200:
                    return None
                    
                data = response.json()
                if not data or not data.get(str(app_id)) or not data[str(app_id)].get("success"):
                    return None
                    
                game_data = data[str(app_id)]["data"]
                
                title = game_data.get("name", f"Unknown Game {app_id}")
                is_free = game_data.get("is_free", False)
                
                if is_free:
                    return {
                        "title": title,
                        "current_price": 0.0,
                        "initial_price": 0.0,
                        "discount_percent": 0
                    }
                    
                price_overview = game_data.get("price_overview")
                if not price_overview:
                    return {
                        "title": title,
                        "current_price": 0.0,
                        "initial_price": 0.0,
                        "discount_percent": 0
                    }
                    
                return {
                    "title": title,
                    "current_price": price_overview.get("final", 0) / 100.0,
                    "initial_price": price_overview.get("initial", 0) / 100.0,
                    "discount_percent": price_overview.get("discount_percent", 0)
                }
                
            except Exception:
                return None

steam_service = SteamService()