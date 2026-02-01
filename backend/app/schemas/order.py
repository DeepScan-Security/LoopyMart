from pydantic import BaseModel


class OrderCreate(BaseModel):
    shipping_address: str


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_order: float
    product_name: str

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    total: float
    status: str
    shipping_address: str
    items: list[OrderItemResponse] = []

    class Config:
        from_attributes = True


OrderResponse.model_rebuild()
