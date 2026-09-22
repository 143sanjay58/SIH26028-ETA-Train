import sys, asyncio, traceback
sys.path.insert(0, 'E:\\External_hackathon_train')

from backend.app.database.session import AsyncSessionLocal
from backend.app.services.eta_service import ETAService

async def main():
    db = AsyncSessionLocal()
    try:
        service = ETAService(db)
        result = await service.predict_eta('12345', include_explanations=True, include_uncertainty=True)
        print('OK:', result)
    except Exception as e:
        traceback.print_exc()
    finally:
        await db.close()

asyncio.run(main())