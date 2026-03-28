"""Test helpers to create model instances."""

from __future__ import annotations

from app.models import AppService, Hardware, VM, db


def create_hardware(
    *,
    name: str = "Test Host",
    hostname: str | None = None,
    ip_address: str | None = None,
    mac_address: str | None = None,
    **kwargs,
) -> Hardware:
    hw = Hardware(
        name=name,
        hostname=hostname,
        ip_address=ip_address,
        mac_address=mac_address,
        **kwargs,
    )
    db.session.add(hw)
    db.session.commit()
    return hw


def create_vm(
    *,
    hardware_id: int,
    name: str = "Test VM",
    hostname: str | None = None,
    ip_address: str | None = None,
    mac_address: str | None = None,
    **kwargs,
) -> VM:
    vm = VM(
        hardware_id=hardware_id,
        name=name,
        hostname=hostname,
        ip_address=ip_address,
        mac_address=mac_address,
        **kwargs,
    )
    db.session.add(vm)
    db.session.commit()
    return vm


def create_app_service(
    *,
    name: str = "Test App",
    hardware_id: int | None = None,
    vm_id: int | None = None,
    hostname: str | None = None,
    ip_address: str | None = None,
    port: int | None = None,
    https: bool = False,
    **kwargs,
) -> AppService:
    app = AppService(
        name=name,
        hardware_id=hardware_id,
        vm_id=vm_id,
        hostname=hostname,
        ip_address=ip_address,
        port=port,
        https=https,
        **kwargs,
    )
    db.session.add(app)
    db.session.commit()
    return app
