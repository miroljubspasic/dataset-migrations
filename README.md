1. copy/edit .env.example -> .env (in app directory)

2. install dataset command

* 1st method - python (tested with v3.8)
  * cd app
  * pip install --editable .
  * dataset start --type=customers
  * dataset start --type=orders
  * dataset start --type=giftcards
  * dataset start --type=sor_subscriptions
  * dataset start --type=sor_orders

-----

* 2nd method - Docker

  * docker-compose build 
  * docker-compose up -d
  * docker exec -it app dataset start --type=customers
  * docker exec -it app dataset start --type=orders
  * docker exec -it app dataset start --type=giftcards
  * docker exec -it app dataset start --type=sor_subscriptions
  * docker exec -it app dataset start --type=sor_orders

---

