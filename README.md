## Endpoints

> to get JWT Token
>- api/v1/token/

>refresh access token
>- api/v1/token/refresh/

> register
>- api/v1/register/

> get weather by city name
>- api/v1/weather/<city_name>/

> get all subscriptions
>- api/v1/subscriptions/

> create a subscription for a city with a period of notification. Example: api/v1/subscriptions/London/12/
>- api/v1/subscriptions/<city_name>/<period_of_notification>/>

> update a subscription to get another period of notification. Example: api/v1/subscriptions/London/5/
>- api/v1/subscriptions/<city_name>/<period_of_notification>/

> delete subscription
>- api/v1/subscriptions/<city_name>/
