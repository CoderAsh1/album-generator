import asyncio
import logging
import httpx
from typing import Optional, Dict, Any, List
from config import KIE_API_KEY, KIE_BASE_URL, KIE_IMAGE_MODEL

logger = logging.getLogger("album_maker.kie")

# Event-specific high-aesthetic design prompts for gpt-image-2-image-to-image
DESIGN_PROMPTS = {
    "wedding": (
        "High-end panoramic Indian wedding photobook spread design, royal palace marble architecture, "
        "reflective water lake, ornate white carved temple pillars and mandap backdrop, soft romantic atmospheric haze, "
        "luxury editorial wedding color grading, warm golden hour tones, pristine 8k print quality, seamless scenic blend."
    ),
    "haldi": (
        "Vibrant luxury Indian Haldi ceremony photobook backdrop, lush marigold floral curtains, traditional brass urlis with yellow petals, "
        "bright festive sunshine, warm rich golden hues, joyful cinematic lighting, high-end wedding album aesthetic."
    ),
    "mehendi": (
        "Intricate boho-chic Mehendi festival photobook backdrop, colorful floral tassels, botanical green foliage, "
        "draped pastel fabrics, glowing fairy lights, warm earthy and festive celebration color grading."
    ),
    "sangeet": (
        "Grand Sangeet musical night wedding album spread, sparkling bokeh lights, illuminated royal ballroom stage, "
        "deep sapphire navy and warm gold ambient glow, dramatic cinematic motion and festive elegance."
    ),
    "reception": (
        "Imperial luxury wedding reception banquet backdrop, crystal chandeliers, floral chandeliers, opulent gold arches, "
        "champagne and warm amber mood lighting, ultra-clean high-end editorial wedding photobook quality."
    )
}

class KieClient:
    def __init__(self, api_key: str = KIE_API_KEY):
        self.api_key = api_key
        self.base_url = KIE_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def get_prompt_for_event(self, event_name: str) -> str:
        """Returns tailored design prompt based on event name."""
        lower = event_name.lower()
        for k, p in DESIGN_PROMPTS.items():
            if k in lower:
                return p
        return DESIGN_PROMPTS["wedding"]

    async def create_image_to_image_task(
        self,
        prompt: str,
        input_urls: List[str],
        aspect_ratio: str = "auto"
    ) -> Optional[str]:
        """
        Creates a task using Kie.ai model gpt-image-2-image-to-image
        Returns taskId if accepted.
        """
        url = f"{self.base_url}/createTask"
        payload = {
            "model": KIE_IMAGE_MODEL,
            "input": {
                "prompt": prompt,
                "input_urls": input_urls,
                "aspect_ratio": aspect_ratio
            }
        }
        
        try:
            logger.info(f"Submitting KIE task with model={KIE_IMAGE_MODEL}, prompt='{prompt[:60]}...'")
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"KIE createTask response: {data}")
                    task_id = data.get("taskId") or (data.get("data") or {}).get("taskId")
                    return task_id
                else:
                    logger.error(f"KIE createTask failed ({response.status_code}): {response.text}")
                    return None
        except Exception as e:
            logger.error(f"KIE createTask exception: {e}")
            return None

    async def poll_task_result(
        self,
        task_id: str,
        max_attempts: int = 40,
        delay_seconds: float = 3.0
    ) -> Optional[Dict[str, Any]]:
        """
        Polls recordInfo endpoint until task reaches 'success' or 'fail'.
        """
        url = f"{self.base_url}/recordInfo?taskId={task_id}"
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                for attempt in range(max_attempts):
                    response = await client.get(url, headers=self.headers)
                    if response.status_code == 200:
                        data = response.json()
                        task_data = data.get("data") or data
                        status = task_data.get("status") or task_data.get("state")
                        
                        logger.info(f"Polling KIE task {task_id} (attempt {attempt+1}/{max_attempts}): status={status}")
                        
                        if status in ["success", "completed", "done"]:
                            return task_data
                        elif status in ["fail", "failed", "error"]:
                            logger.error(f"KIE task {task_id} failed: {task_data}")
                            return None
                    
                    await asyncio.sleep(delay_seconds)
                
                logger.warning(f"KIE task {task_id} timed out after {max_attempts * delay_seconds}s")
                return None
        except Exception as e:
            logger.error(f"KIE polling exception: {e}")
            return None

    async def transform_image(
        self,
        image_url: str,
        prompt: Optional[str] = None,
        event_name: str = "wedding",
        aspect_ratio: str = "16:9"
    ) -> Optional[str]:
        """
        Convenience method to transform an image using Kie.ai and return the output image URL.
        """
        if not prompt:
            prompt = self.get_prompt_for_event(event_name)
            
        task_id = await self.create_image_to_image_task(
            prompt=prompt,
            input_urls=[image_url],
            aspect_ratio=aspect_ratio
        )
        if not task_id:
            return None
        
        result = await self.poll_task_result(task_id)
        if result:
            outputs = result.get("output") or result.get("output_urls") or result.get("result")
            if isinstance(outputs, list) and len(outputs) > 0:
                return outputs[0]
            elif isinstance(outputs, str):
                return outputs
            elif isinstance(result.get("response"), dict):
                return result["response"].get("url")
        return None

# Singleton client
kie_client = KieClient()
