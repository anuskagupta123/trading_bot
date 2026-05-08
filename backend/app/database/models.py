from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Date
from sqlalchemy.sql import func
from .database import Base
from datetime import date

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Broker(Base):
    __tablename__ = "brokers"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)  # links to users table
    broker_name = Column(String)  # "zerodha" or "shoonya"
    api_key = Column(String)
    api_secret = Column(String)
    access_token = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    action = Column(String)  # "BUY" or "SELL"
    quantity = Column(Integer)
    broker_id = Column(Integer, nullable=True)  # which broker executed
    order_id = Column(String, nullable=True)  # Zerodha order ID
    status = Column(String)  # "success", "failed", or "pending"
    error_message = Column(String, nullable=True)
    received_at = Column(DateTime(timezone=True), server_default=func.now())
    executed_at = Column(DateTime(timezone=True), nullable=True)

class RiskSettings(Base):
    __tablename__ = "risk_settings"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    max_loss_per_day = Column(Float, default=5000.0)  # in rupees
    max_trades_per_day = Column(Integer, default=10)
    default_stop_loss_pct = Column(Float, default=1.0)  # 1%
    default_target_pct = Column(Float, default=2.0)    # 2%
    trailing_sl_enabled = Column(Boolean, default=False)
    exit_all_at_close = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    action = Column(String)  # "BUY" or "SELL"
    quantity = Column(Integer)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)  # Profit/Loss
    pnl_pct = Column(Float, nullable=True)  # P&L %
    status = Column(String, default="open")  # "open", "closed", "cancelled"
    order_id = Column(String)  # Zerodha order ID
    exit_order_id = Column(String, nullable=True)
    trade_date = Column(Date, default=date.today)
    entry_time = Column(DateTime(timezone=True), server_default=func.now())
    exit_time = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)

class VirtualWallet(Base):
    __tablename__ = "virtual_wallets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True)
    balance = Column(Float, default=100000.0)  # Start with ₹1,00,000
    total_pnl = Column(Float, default=0.0)  # Cumulative P&L
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PaperTrade(Base):
    __tablename__ = "paper_trades"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    action = Column(String)  # "BUY" or "SELL"
    quantity = Column(Integer)
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    pnl = Column(Float, nullable=True)  # Profit/Loss
    pnl_pct = Column(Float, nullable=True)  # P&L percentage
    status = Column(String, default="open")  # "open" or "closed"
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)