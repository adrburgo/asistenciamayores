from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from .. import contacts_store

router = APIRouter()
templates = Jinja2Templates(directory="/app/src/templates")


@router.get("/contacts", response_class=HTMLResponse)
async def contacts_page(request: Request):  # noqa: ANN001
    data = contacts_store.load()
    return templates.TemplateResponse("contacts.html", {
        "request": request,
        "emergency_phone": data.get("emergency_phone", "112"),
        "contacts": data.get("contacts", []),
        "active": "contacts",
    })


@router.post("/contacts/emergency")
async def update_emergency(phone: str = Form(...)):
    data = contacts_store.load()
    data["emergency_phone"] = phone.strip()
    contacts_store.save(data)
    return RedirectResponse("/contacts", status_code=303)


@router.post("/contacts/add")
async def add_contact(name: str = Form(...), phone: str = Form(...)):
    data = contacts_store.load()
    data.setdefault("contacts", []).append({
        "name": name.strip(),
        "phone": phone.strip(),
    })
    contacts_store.save(data)
    return RedirectResponse("/contacts", status_code=303)


@router.post("/contacts/{index}/delete")
async def delete_contact(index: int):
    data = contacts_store.load()
    contacts = data.get("contacts", [])
    if 0 <= index < len(contacts):
        contacts.pop(index)
        data["contacts"] = contacts
        contacts_store.save(data)
    return RedirectResponse("/contacts", status_code=303)
