#!/usr/bin/env python3
"""Health check script for JobPilot services."""

import sys
import asyncio
import httpx
import asyncpg
import redis


async def check_backend():
    """Check if backend API is responding."""
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:8000/health", timeout=5.0)
            return r.status_code == 200
    except Exception:
        return False


async def check_database():
    """Check PostgreSQL connection."""
    try:
        conn = await asyncpg.connect(
            "postgresql://jobpilot:jobpilot_pass@localhost:5432/jobpilot_db"
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception:
        return False


def check_redis():
    """Check Redis connection."""
    try:
        r = redis.Redis(host="localhost", port=6379, socket_timeout=5)
        return r.ping()
    except Exception:
        return False


def check_rabbitmq():
    """Check RabbitMQ connection."""
    try:
        import pika
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host="localhost",
                port=5672,
                credentials=pika.PlainCredentials("jobpilot", "rabbitmq_pass"),
                connection_attempts=1,
                socket_timeout=5,
            )
        )
        connection.close()
        return True
    except Exception:
        return False


async def main():
    """Run all health checks."""
    checks = {
        "Backend API": await check_backend(),
        "PostgreSQL": await check_database(),
        "Redis": check_redis(),
        "RabbitMQ": check_rabbitmq(),
    }

    all_healthy = True
    for service, healthy in checks.items():
        status = "OK" if healthy else "FAIL"
        print(f"  {service}: {status}")
        if not healthy:
            all_healthy = False

    if all_healthy:
        print("\nAll services healthy.")
        sys.exit(0)
    else:
        print("\nSome services are unhealthy!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
