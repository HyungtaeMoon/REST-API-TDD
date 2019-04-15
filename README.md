## RECIPE APP TDD

\#Python \#Django \#Docker \#Docker-compose \#Travis-Ci

RUN

```python
docker-compose up

docker-compose run --rm app sh -c "python manage.py test"
```


### REST-API
--

#### User Create(회원가입) / POST

- status: 200 OK
- required: email, password, name


Sample Request:

```python
URL: http://localhost:8000/api/user/create/


Headers
{
	key: Content-Type
	value: application/x-www-form-urlencoded
}

Body
{
	"email": "test2@master.com",
	"password": "*********",
	"name": "karl"
}

```

Sample Response:

```python
{
    "email": "test2@master.com",
    "name": "karl"
}
```

-

#### User Token (토큰 발급) / POST

- status: 200 OK
- 브라우저에서 Token 값을 항상 가지고 있도록 modheader 플러그인 사용
	- <a href="https://chrome.google.com/webstore/detail/modheader/idgpnmonknjnojddfkpgkljpfnnfcklj" target="_blank">modheader (토큰 관리)</a>

![modheader](./modheader.png)


Sample Request:

```
URL: http://localhost:8000/api/user/token/


- Headers
{
	key: Content-Type
	value: application/x-www-form-urlencoded
}


- Body
{
	"email": "test2@master.com",
	"password": "*********",
	"name": "karl" #optional
}
```

Sample Response:

```
{
    "token": "64a7c0ae46888ee6f758d0684ff29dc3ab8ef625"
}

```


#### User Token 확인 / `GET`, PUT

- 회원정보 `확인` /변경(비밀번호, 이름)
- status: 200 OK
- 발급받은 `Token` 을 modheader 플러그인을 사용하여 토큰 값을 저장


Sample Request:

```
URL: http://localhost:8000/api/user/me/


- Headers
{
	key: Authorization
	value: token 64a7c0ae46888ee6f758d0684ff29dc3ab8e****
}


- Body
{
	None
}
```

Sample Response:

```
{
    "email": "test2@master.com",
    "name": "karl"
}
```

--

#### User Token 확인 / GET, `PUT`

- 회원정보 확인 /`변경(비밀번호, 이름)`
- status: 200 OK
- 발급받은 `Token` 을 modheader 플러그인을 사용하여 토큰 값을 저장


Sample Request:

```
URL: http://localhost:8000/api/user/me/


- Headers
{
	key: Authorization
	value: token 64a7c0ae46888ee6f758d0684ff29dc3ab8e****
}


- Body
{
	"email": "test2@master.com", #required
	"password": "*********", #required
	"name": "karl" #required
}
```

Sample Response:

```
{
    "email": "test2@master.com",
    "name": "karl"
}
```


--

#### API Root / GET

- 레시피/태그/재료 확인(루트 경로)
- status: 200 OK


Sample Request:

```
URL: http://localhost:8000/api/root/


- Headers
{
	None
}


- Body
{
	None
}
```

Sample Response:

```
{
    "tags": "http://localhost:8000/api/recipe/tags/",
    "ingredients": "http://localhost:8000/api/recipe/ingredients/",
    "recipes": "http://localhost:8000/api/recipe/recipes/"
}
```

--

#### Recipe Create / POST

- 레시피 생성
- status: 201 CREATED


Sample Request:

```
URL: http://localhost:8000/api/recipe/recipes/


- Headers
{
	key: Authorization
	value: token 64a7c0ae46888ee6f758d0684ff29dc3ab8e****
}


- Body
{
	"title": "김치 볶음밥 만들기" #required,
	"time_minutes": 10.00 #required,
	"price": 7 #required
}
```

Sample Response:

```
{
    "id": 5,
    "title": "김치볶음밥 만들기",
    "ingredients": [],
    "tags": [],
    "time_minutes": 10,
    "price": "7.00",
    "link": ""
}
```

--

#### Recipe content 수정 / PATCH
: 일부 자원만 수정하기 때문에 PATCH

- title, time_minutes, price, link, tag, ingredient 특정 필드만 입력하여 수정
- status: 200 OK


Sample Request:

```
URL: http://localhost:8000/api/recipe/recipes/<int:recipe_pk>/


- Headers
{
	key: Authorization
	value: token 64a7c0ae46888ee6f758d0684ff29dc3ab8e****
}


- Body
{
	"title": "까르보나라 만들기",
	"ingredient": 3 #강황
}
```

Sample Response:

```
{
    "id": 5,
    "title": "까르보나라 만들기",
    "ingredients": [
        3
    ],
    "tags": [],
    "time_minutes": 10,
    "price": "6.00",
    "link": ""
}
```

--

#### Tag, Ingredient / `POST`, GET

- tag, ingredient 생성
	- 2개의 자원 모두 동일한 방식으로 생성/조회 가능
- status: 201 CREATED


Sample Request:

```
URL: http://localhost:8000/api/recipe/ingredients/


- Headers
{
	key: Authorization
	value: token 64a7c0ae46888ee6f758d0684ff29dc3ab8e****
}


- Body
{
	"name": "양배추" #required
}
```

Sample Response:

```
{
    "id": 5,
    "name": "양배추"
}
```

--


#### Tag, Ingredient / POST, `GET`

- tag, ingredient 조회
	- 2개의 자원 모두 동일한 방식으로 생성/조회 가능
- status: 200 OK


Sample Request:

```
URL: http://localhost:8000/api/recipe/ingredients/


- Headers
{
	key: Authorization
	value: token 64a7c0ae46888ee6f758d0684ff29dc3ab8e****
}


- Body
{
	None
}
```

Sample Response:

```
[
    {
        "id": 5,
        "name": "양배추"
    },

]
```
