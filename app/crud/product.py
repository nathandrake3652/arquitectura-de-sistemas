from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.product import Product
from app.schemas.product import ProductCreate


def create_product(db: Session, payload: ProductCreate) -> Product:
    try:
        product = Product(
            name=payload.name,
            description=payload.description,
            price=payload.price,
        )
        db.add(product)
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Product with name '{payload.name}' already exists")


def get_products(db: Session) -> list[Product]:
    return db.query(Product).all()


def get_product(db: Session, product_id: int) -> Product:
    return db.query(Product).filter(Product.id == product_id).first()


def update_product(db: Session, product_id: int, payload: ProductCreate) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product with id {product_id} does not exist")
    
    try:
        product.name = payload.name
        product.description = payload.description
        product.price = payload.price
        db.commit()
        db.refresh(product)
        return product
    except IntegrityError:
        db.rollback()
        raise ValueError(f"Product with name '{payload.name}' already exists")


def delete_product(db: Session, product_id: int) -> bool:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise ValueError(f"Product with id {product_id} does not exist")
    
    db.delete(product)
    db.commit()
    return True
