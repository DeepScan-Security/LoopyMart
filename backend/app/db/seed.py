"""
Database seeding for initial setup.
Seeds admin user (from env vars) and initial category/product data.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.categories_mongo import category_create, category_get_by_slug
from app.db.coupons_mongo import coupon_seed_default
from app.db.products_mongo import product_create, product_get_by_name
from app.models.user import User


# Category definitions with images
CATEGORIES = [
    {
        "name": "Electronics",
        "slug": "electronics",
        "description": "Electronic gadgets, smartphones, laptops, and devices",
        "image_url": "https://cdn-icons-png.flaticon.com/128/3659/3659898.png",
    },
    {
        "name": "Fashion",
        "slug": "fashion",
        "description": "Clothing, footwear, and fashion accessories for all",
        "image_url": "https://cdn-icons-png.flaticon.com/128/863/863684.png",
    },
    {
        "name": "Home & Kitchen",
        "slug": "home-kitchen",
        "description": "Home appliances, cookware, furniture, and decor",
        "image_url": "https://cdn-icons-png.flaticon.com/128/1698/1698778.png",
    },
    {
        "name": "Books",
        "slug": "books",
        "description": "Fiction, non-fiction, academic, and self-help books",
        "image_url": "https://cdn-icons-png.flaticon.com/128/2702/2702134.png",
    },
    {
        "name": "Sports & Fitness",
        "slug": "sports-fitness",
        "description": "Sports equipment, fitness gear, and outdoor accessories",
        "image_url": "https://cdn-icons-png.flaticon.com/128/857/857418.png",
    },
    {
        "name": "Beauty & Personal Care",
        "slug": "beauty-personal-care",
        "description": "Skincare, haircare, makeup, and grooming products",
        "image_url": "https://cdn-icons-png.flaticon.com/128/1005/1005684.png",
    },
]


# Dummy products organized by category slug
DUMMY_PRODUCTS = {
    "electronics": [
        {
            "name": "iPhone 15 Pro Max 256GB",
            "description": "Latest Apple flagship with A17 Pro chip, titanium design, and advanced 48MP camera system. Features Dynamic Island and always-on display.",
            "price": 159900.00,
            "image_url": "https://picsum.photos/seed/iphone15/400/400",
            "stock": 25,
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "description": "Premium Android smartphone with S Pen, 200MP camera, and Galaxy AI features. Titanium frame with Gorilla Armor display.",
            "price": 134999.00,
            "image_url": "https://picsum.photos/seed/galaxys24/400/400",
            "stock": 30,
        },
        {
            "name": "MacBook Air M3 13-inch",
            "description": "Ultra-thin laptop powered by Apple M3 chip. 18-hour battery life, Liquid Retina display, and fanless design for silent operation.",
            "price": 114900.00,
            "image_url": "https://picsum.photos/seed/macbookair/400/400",
            "stock": 20,
        },
        {
            "name": "Sony WH-1000XM5 Headphones",
            "description": "Industry-leading noise cancellation with exceptional sound quality. 30-hour battery life and speak-to-chat feature.",
            "price": 29990.00,
            "image_url": "https://picsum.photos/seed/sonywh1000/400/400",
            "stock": 45,
        },
        {
            "name": "Apple Watch Series 9",
            "description": "Advanced health monitoring with ECG and blood oxygen sensors. Double tap gesture and bright always-on Retina display.",
            "price": 41900.00,
            "image_url": "https://picsum.photos/seed/applewatch9/400/400",
            "stock": 35,
        },
        {
            "name": "iPad Pro 12.9-inch M2",
            "description": "Professional tablet with M2 chip, Liquid Retina XDR display, and Apple Pencil hover support. Perfect for creative professionals.",
            "price": 112900.00,
            "image_url": "https://picsum.photos/seed/ipadpro/400/400",
            "stock": 18,
        },
        {
            "name": "JBL Flip 6 Bluetooth Speaker",
            "description": "Portable waterproof speaker with powerful JBL Original Pro Sound. 12-hour playtime and PartyBoost feature.",
            "price": 9999.00,
            "image_url": "https://picsum.photos/seed/jblflip6/400/400",
            "stock": 60,
        },
    ],
    "fashion": [
        {
            "name": "Levi's 511 Slim Fit Jeans",
            "description": "Classic slim fit jeans with stretch comfort. Made from premium denim with a modern silhouette that sits below the waist.",
            "price": 3499.00,
            "image_url": "https://picsum.photos/seed/levisjeans/400/400",
            "stock": 80,
        },
        {
            "name": "Nike Air Max 270 Sneakers",
            "description": "Iconic lifestyle sneakers with the largest Air unit yet for all-day comfort. Mesh upper for breathability.",
            "price": 12995.00,
            "image_url": "https://picsum.photos/seed/nikeairmax/400/400",
            "stock": 40,
        },
        {
            "name": "Allen Solly Formal Shirt",
            "description": "Premium cotton formal shirt with wrinkle-resistant fabric. Perfect for office wear with a comfortable regular fit.",
            "price": 1799.00,
            "image_url": "https://picsum.photos/seed/formalshirt/400/400",
            "stock": 100,
        },
        {
            "name": "Fossil Grant Chronograph Watch",
            "description": "Classic chronograph watch with genuine leather strap. Roman numeral markers and 24-hour subdial for timeless style.",
            "price": 8995.00,
            "image_url": "https://picsum.photos/seed/fossilwatch/400/400",
            "stock": 25,
        },
        {
            "name": "Wildcraft Backpack 35L",
            "description": "Durable travel backpack with multiple compartments and laptop sleeve. Water-resistant fabric and padded straps.",
            "price": 2499.00,
            "image_url": "https://picsum.photos/seed/backpack/400/400",
            "stock": 55,
        },
        {
            "name": "Puma Essential Logo T-Shirt",
            "description": "Comfortable cotton t-shirt with iconic Puma branding. Regular fit with ribbed crew neck for everyday wear.",
            "price": 999.00,
            "image_url": "https://picsum.photos/seed/pumatshirt/400/400",
            "stock": 150,
        },
    ],
    "home-kitchen": [
        {
            "name": "Prestige Iris 750W Mixer Grinder",
            "description": "Powerful mixer grinder with 3 stainless steel jars. Overload protection and ergonomic handles for easy use.",
            "price": 3299.00,
            "image_url": "https://picsum.photos/seed/mixergrinder/400/400",
            "stock": 35,
        },
        {
            "name": "Philips Air Fryer HD9252",
            "description": "Healthy cooking with 90% less fat using Rapid Air technology. 4.1L capacity with digital touchscreen.",
            "price": 8999.00,
            "image_url": "https://picsum.photos/seed/airfryer/400/400",
            "stock": 28,
        },
        {
            "name": "Nilkamal Plastic Storage Cabinet",
            "description": "Multi-purpose storage cabinet with 4 shelves. Durable plastic construction, easy assembly required.",
            "price": 4599.00,
            "image_url": "https://picsum.photos/seed/storagecabinet/400/400",
            "stock": 20,
        },
        {
            "name": "Pigeon Favourite 3 Burner Gas Stove",
            "description": "Efficient brass burners with powder-coated body. Spill-proof design and high-quality pan supports.",
            "price": 2499.00,
            "image_url": "https://picsum.photos/seed/gasstove/400/400",
            "stock": 40,
        },
        {
            "name": "Cello Opalware Dinner Set 19pcs",
            "description": "Elegant bone-ash free opalware dinner set. Microwave safe, chip resistant, and dishwasher safe.",
            "price": 1299.00,
            "image_url": "https://picsum.photos/seed/dinnerset/400/400",
            "stock": 45,
        },
    ],
    "books": [
        {
            "name": "Atomic Habits by James Clear",
            "description": "The #1 New York Times bestseller on building good habits and breaking bad ones. Proven strategies for daily improvement.",
            "price": 499.00,
            "image_url": "https://picsum.photos/seed/atomichabits/400/400",
            "stock": 200,
        },
        {
            "name": "The Psychology of Money",
            "description": "Morgan Housel explores the strange ways people think about money. Timeless lessons on wealth, greed, and happiness.",
            "price": 399.00,
            "image_url": "https://picsum.photos/seed/psychmoney/400/400",
            "stock": 180,
        },
        {
            "name": "Rich Dad Poor Dad",
            "description": "Robert Kiyosaki's classic on financial literacy and building wealth. Learn what the rich teach their kids about money.",
            "price": 350.00,
            "image_url": "https://picsum.photos/seed/richdad/400/400",
            "stock": 220,
        },
        {
            "name": "The Alchemist by Paulo Coelho",
            "description": "A magical story of Santiago, an Andalusian shepherd boy who dreams of worldly treasure. A masterpiece on following your dreams.",
            "price": 299.00,
            "image_url": "https://picsum.photos/seed/alchemist/400/400",
            "stock": 250,
        },
        {
            "name": "Clean Code by Robert C. Martin",
            "description": "A handbook of agile software craftsmanship. Learn principles and best practices for writing clean, maintainable code.",
            "price": 2999.00,
            "image_url": "https://picsum.photos/seed/cleancode/400/400",
            "stock": 50,
        },
    ],
    "sports-fitness": [
        {
            "name": "Fitbit Charge 6 Fitness Tracker",
            "description": "Advanced fitness tracker with built-in GPS and heart rate monitoring. Track sleep, stress, and workouts with precision.",
            "price": 14999.00,
            "image_url": "https://picsum.photos/seed/fitbit/400/400",
            "stock": 30,
        },
        {
            "name": "Cosco Cricket Bat English Willow",
            "description": "Premium English willow cricket bat for professional play. Full size with traditional handle grip.",
            "price": 4599.00,
            "image_url": "https://picsum.photos/seed/cricketbat/400/400",
            "stock": 25,
        },
        {
            "name": "Nivia Pro Volleyball",
            "description": "Official size and weight volleyball for competitive play. Durable PU leather with excellent grip and flight stability.",
            "price": 899.00,
            "image_url": "https://picsum.photos/seed/volleyball/400/400",
            "stock": 70,
        },
        {
            "name": "PowerMax Fitness Treadmill",
            "description": "Motorized treadmill with 4HP peak motor. 12 preset programs, LCD display, and foldable design for home use.",
            "price": 34999.00,
            "image_url": "https://picsum.photos/seed/treadmill/400/400",
            "stock": 10,
        },
        {
            "name": "Strauss Yoga Mat 6mm",
            "description": "Anti-skid yoga mat with extra cushioning for joints. Lightweight, eco-friendly material with carrying strap.",
            "price": 599.00,
            "image_url": "https://picsum.photos/seed/yogamat/400/400",
            "stock": 100,
        },
    ],
    "beauty-personal-care": [
        {
            "name": "L'Oreal Paris Revitalift Serum",
            "description": "Anti-aging serum with 1.5% Hyaluronic Acid. Hydrates skin and reduces wrinkles for a youthful glow.",
            "price": 899.00,
            "image_url": "https://picsum.photos/seed/lorealserum/400/400",
            "stock": 65,
        },
        {
            "name": "Philips BT3211 Beard Trimmer",
            "description": "Cordless beard trimmer with 20 length settings. Self-sharpening blades and 60-minute runtime.",
            "price": 1499.00,
            "image_url": "https://picsum.photos/seed/beardtrimmer/400/400",
            "stock": 45,
        },
        {
            "name": "Maybelline Fit Me Foundation",
            "description": "Lightweight foundation with SPF 18 that fits your skin tone. Natural matte finish with pore-minimizing effect.",
            "price": 399.00,
            "image_url": "https://picsum.photos/seed/foundation/400/400",
            "stock": 90,
        },
        {
            "name": "Dove Shampoo Intense Repair 1L",
            "description": "Nourishing shampoo for damaged hair with keratin repair actives. Strengthens and smoothens hair from root to tip.",
            "price": 499.00,
            "image_url": "https://picsum.photos/seed/doveshampoo/400/400",
            "stock": 120,
        },
        {
            "name": "Nivea Men Deep Impact Face Wash",
            "description": "Activated charcoal face wash for deep cleansing. Removes dirt, oil, and impurities for fresh skin.",
            "price": 249.00,
            "image_url": "https://picsum.photos/seed/niveafacewash/400/400",
            "stock": 150,
        },
    ],
}


async def seed_categories() -> dict[str, str]:
    """
    Seed all categories and return a mapping of slug to category ID.
    Updates image_url for existing categories if missing.
    """
    from app.db.categories_mongo import category_update
    
    category_map = {}
    for cat_data in CATEGORIES:
        existing = await category_get_by_slug(cat_data["slug"])
        if existing:
            category_map[cat_data["slug"]] = existing["id"]
            # Update image_url if it's missing or different
            if existing.get("image_url") != cat_data.get("image_url"):
                await category_update(
                    existing["id"],
                    image_url=cat_data.get("image_url"),
                )
        else:
            created = await category_create(
                name=cat_data["name"],
                slug=cat_data["slug"],
                description=cat_data["description"],
                image_url=cat_data.get("image_url"),
            )
            category_map[cat_data["slug"]] = created["id"]
    return category_map


async def seed_products(category_map: dict[str, str]) -> None:
    """
    Seed all dummy products using the category map.
    Only creates products that don't already exist (by name).
    """
    for category_slug, products in DUMMY_PRODUCTS.items():
        category_id = category_map.get(category_slug)
        if not category_id:
            continue
        for product in products:
            # Check if product already exists by name
            existing = await product_get_by_name(product["name"])
            if existing:
                continue  # Skip if product already exists
            await product_create(
                name=product["name"],
                description=product["description"],
                price=product["price"],
                image_url=product["image_url"],
                stock=product["stock"],
                category_id=category_id,
            )


async def seed_db(db: AsyncSession) -> None:
    """
    Seed the database with initial data.
    
    - Creates admin user if ADMIN_EMAIL and ADMIN_PASSWORD are set in env vars
    - Creates categories in MongoDB
    - Creates dummy products if no products exist
    - Seeds default coupons
    """
    # SQL: Create admin user if credentials are provided
    if settings.admin_email and settings.admin_password:
        result = await db.execute(select(User).where(User.email == settings.admin_email))
        existing_admin = result.scalar_one_or_none()
        if not existing_admin:
            admin_user = User(
                email=settings.admin_email,
                hashed_password=get_password_hash(settings.admin_password),
                full_name=settings.admin_name,
                is_admin=True,
            )
            db.add(admin_user)
            await db.flush()

    # MongoDB: Seed categories
    category_map = await seed_categories()

    # MongoDB: Seed products
    await seed_products(category_map)

    # MongoDB: Seed default coupons
    await coupon_seed_default()
