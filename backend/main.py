from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from typing import Optional
import secrets

from .database import engine, get_db, Base
from . import models

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AnzorikEPT API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== INITIAL UPGRADES ======================
INITIAL_UPGRADES = [
    {
        "name": "Кибер-когти",
        "description": "+1 к силе тапа",
        "category": "tap",
        "base_price": 50,
        "price_multiplier": 1.4,
        "effect_value": 1.0,
        "effect_type": "tap_power",
        "icon": "爪"
    },
    {
        "name": "Неоновый импульс",
        "description": "+2 к силе тапа",
        "category": "tap",
        "base_price": 300,
        "price_multiplier": 1.45,
        "effect_value": 2.0,
        "effect_type": "tap_power",
        "icon": "⚡"
    },
    {
        "name": "Огненный рывок",
        "description": "+5 к силе тапа",
        "category": "tap",
        "base_price": 1500,
        "price_multiplier": 1.5,
        "effect_value": 5.0,
        "effect_type": "tap_power",
        "icon": "🔥"
    },
    {
        "name": "Майнинг-ферма",
        "description": "+10 монет в час",
        "category": "passive",
        "base_price": 200,
        "price_multiplier": 1.4,
        "effect_value": 10.0,
        "effect_type": "passive_income",
        "icon": "🖥️"
    },
    {
        "name": "Кибер-узел",
        "description": "+50 монет в час",
        "category": "passive",
        "base_price": 1200,
        "price_multiplier": 1.45,
        "effect_value": 50.0,
        "effect_type": "passive_income",
        "icon": "📡"
    },
    {
        "name": "Квантовый реактор",
        "description": "+200 монет в час",
        "category": "passive",
        "base_price": 8000,
        "price_multiplier": 1.5,
        "effect_value": 200.0,
        "effect_type": "passive_income",
        "icon": "⚛️"
    },
    {
        "name": "Энергоячейка",
        "description": "+200 к максимуму энергии",
        "category": "energy",
        "base_price": 400,
        "price_multiplier": 1.4,
        "effect_value": 200.0,
        "effect_type": "max_energy",
        "icon": "🔋"
    },
    {
        "name": "Плазменный аккумулятор",
        "description": "+500 к максимуму энергии",
        "category": "energy",
        "base_price": 2500,
        "price_multiplier": 1.45,
        "effect_value": 500.0,
        "effect_type": "max_energy",
        "icon": "💜"
    },
]


def init_upgrades(db: Session):
    if db.query(models.Upgrade).count() == 0:
        for up in INITIAL_UPGRADES:
            db.add(models.Upgrade(**up))
        db.commit()


@app.on_event("startup")
def on_startup():
    db = next(get_db())
    init_upgrades(db)
    db.close()


# ====================== HELPERS ======================

def generate_referral_code(telegram_id: int) -> str:
    return hashlib.md5(f"anzorik_{telegram_id}_{secrets.token_hex(4)}".encode()).hexdigest()[:8].upper()


def calculate_energy(user: models.User) -> int:
    now = datetime.utcnow()
    elapsed = (now - user.last_energy_update).total_seconds()
    # 1 energy every 3 seconds
    recovered = int(elapsed / 3)
    new_energy = min(user.max_energy, user.energy + recovered)
    return new_energy


def calculate_passive(user: models.User) -> float:
    now = datetime.utcnow()
    hours = (now - user.last_passive_claim).total_seconds() / 3600
    return user.passive_income * hours


def get_upgrade_price(upgrade: models.Upgrade, level: int) -> float:
    return upgrade.base_price * (upgrade.price_multiplier ** level)


# ====================== API ======================

@app.post("/api/user/init")
def init_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    referral_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()

    if not user:
        user = models.User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=generate_referral_code(telegram_id),
            balance=100.0,  # стартовый бонус
        )

        # Рефералка
        if referral_code:
            referrer = db.query(models.User).filter(models.User.referral_code == referral_code.upper()).first()
            if referrer and referrer.telegram_id != telegram_id:
                user.referred_by = referrer.telegram_id
                referrer.balance += 500  # бонус за реферала
                db.add(referrer)

        db.add(user)
        db.commit()
        db.refresh(user)

        # Создаём записи прокачек
        upgrades = db.query(models.Upgrade).all()
        for up in upgrades:
            db.add(models.UserUpgrade(user_id=user.id, upgrade_id=up.id, level=0))
        db.commit()

    # Обновляем энергию и пассивный доход
    energy = calculate_energy(user)
    passive = calculate_passive(user)

    if energy != user.energy:
        user.energy = energy
        user.last_energy_update = datetime.utcnow()

    if passive > 0:
        user.balance += passive
        user.total_earned += passive
        user.last_passive_claim = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Собираем данные по прокачкам
    user_upgrades = db.query(models.UserUpgrade).filter(models.UserUpgrade.user_id == user.id).all()
    upgrades_data = []
    for uu in user_upgrades:
        up = uu.upgrade
        upgrades_data.append({
            "id": up.id,
            "name": up.name,
            "description": up.description,
            "category": up.category,
            "icon": up.icon,
            "level": uu.level,
            "price": get_upgrade_price(up, uu.level),
            "effect_value": up.effect_value,
            "effect_type": up.effect_type,
            "max_level": up.max_level
        })

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": round(user.balance, 2),
        "total_earned": round(user.total_earned, 2),
        "tap_power": user.tap_power,
        "energy": user.energy,
        "max_energy": user.max_energy,
        "passive_income": user.passive_income,
        "referral_code": user.referral_code,
        "upgrades": upgrades_data
    }


@app.post("/api/tap")
def tap(telegram_id: int, count: int = 1, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    energy = calculate_energy(user)
    if energy < count:
        count = energy

    if count <= 0:
        return {"success": False, "message": "Недостаточно энергии", "energy": energy}

    earned = user.tap_power * count
    user.balance += earned
    user.total_earned += earned
    user.energy = energy - count
    user.last_energy_update = datetime.utcnow()

    db.commit()

    return {
        "success": True,
        "earned": earned,
        "balance": round(user.balance, 2),
        "energy": user.energy,
        "tap_power": user.tap_power
    }


@app.post("/api/buy_upgrade")
def buy_upgrade(telegram_id: int, upgrade_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    uu = db.query(models.UserUpgrade).filter(
        models.UserUpgrade.user_id == user.id,
        models.UserUpgrade.upgrade_id == upgrade_id
    ).first()

    if not uu:
        raise HTTPException(status_code=404, detail="Upgrade not found")

    upgrade = uu.upgrade
    if uu.level >= upgrade.max_level:
        raise HTTPException(status_code=400, detail="Максимальный уровень")

    price = get_upgrade_price(upgrade, uu.level)
    if user.balance < price:
        raise HTTPException(status_code=400, detail="Недостаточно монет")

    user.balance -= price
    uu.level += 1

    # Применяем эффект
    if upgrade.effect_type == "tap_power":
        user.tap_power += upgrade.effect_value
    elif upgrade.effect_type == "passive_income":
        user.passive_income += upgrade.effect_value
    elif upgrade.effect_type == "max_energy":
        user.max_energy += int(upgrade.effect_value)

    db.commit()

    return {
        "success": True,
        "balance": round(user.balance, 2),
        "new_level": uu.level,
        "new_price": get_upgrade_price(upgrade, uu.level),
        "tap_power": user.tap_power,
        "passive_income": user.passive_income,
        "max_energy": user.max_energy
    }


@app.get("/api/leaderboard")
def leaderboard(db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(models.User.total_earned.desc()).limit(20).all()
    return [
        {
            "position": i + 1,
            "username": u.username or u.first_name or f"User{u.telegram_id}",
            "total_earned": round(u.total_earned, 2)
        }
        for i, u in enumerate(users)
    ]


@app.get("/")
def root():
    return {"status": "AnzorikEPT API is running", "version": "1.0.0"}
