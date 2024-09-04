# Store-Site

**It is a full-fledged store app whose main purpose is to sell clothes**

Available pages by User:

- Registration/Authorization (Including via third-party services)
- Home
- Catalog
- Profile
- Order placement using Stripe payment platform

Available pages by Admin:

- View registered accounts
- Creating categories
- Adding products
- Confirmation and processing of paid orders

## Registration/Authorization

**User registration window:**

![Registration Page](static/vendor/img/readme/registration.jpg)

**User authorization window:**

![Registration Page](static/vendor/img/readme/login.jpg)

**Store home page with the ability to redirect to catalog and user profile**

## Home

![Home Page](static/vendor/img/readme/main-page.jpg)

**Store home page with the ability to redirect to catalog and user profile**

## Catalog

![Catalog Page Part 1](static/vendor/img/readme/product-page-1.jpg)
![Catalog Page Part 2](static/vendor/img/readme/product-page-2.jpg)

**A product catalog where the user can view available products and add them to the cart. Also on the left side there are
categories, by which the goods are divided, for a more convenient search.**

## User Profile Page

![Profile Page](static/vendor/img/readme/profile.jpg)

**Here the user can see / change information about themselves. Also, when adding items to cart, those will be shown to
the left of his data:**

![Basket Page](static/vendor/img/readme/profile-basket.jpg)

## Order

![Order Page](static/vendor/img/readme/zakaz.jpg)

**The order is placed as follows, after which, the user is redirected to the Stripe payment page, where after a
successful transaction, the administrator receives a notification and can confirm the order.**

## Admin

**Добавление каталогов и товаров происходит через django admin следующим образом:**

**Добавление категорий:**

![Add Categories Page](static/vendor/img/readme/category-add.jpg)

**Добавление товаров:**

![Add Product Page](static/vendor/img/readme/product-add.jpg)

## Feedback

Please use [telegram](https://t.me/saw_TheMoon) for questions or comments.
