from pydantic import BaseModel


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    image_url: str | None = None
    stock: int = 0
    category_id: int


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    image_url: str | None = None
    stock: int | None = None
    category_id: int | None = None


class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True


class ProductWithCategory(ProductResponse):
    category_name: str | None = None
