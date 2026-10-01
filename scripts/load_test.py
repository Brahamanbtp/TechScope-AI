import asyncio
import os
import time

import httpx


async def main():
    url = os.getenv("TECHSCOPE_URL", "http://127.0.0.1:8000/healthz")
    count = int(os.getenv("LOAD_REQUESTS", "50"))
    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=10) as client:
        responses = await asyncio.gather(*(client.get(url) for _ in range(count)))
    elapsed = time.perf_counter() - start
    successful = sum(response.status_code == 200 for response in responses)
    print({"requests": count, "successful": successful, "seconds": round(elapsed, 3), "rps": round(count / elapsed, 2)})


if __name__ == "__main__":
    asyncio.run(main())