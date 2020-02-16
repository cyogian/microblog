# Setup

1. Clone the repository.
2. run ```pip install -r requirements.txt```
3. Install mysql, elasticsearch and redis.
4. Rename "additional_config.env_" to "additional_config.env"
5. Edit additional_config.env and fill all the environment variables.
6. run ```python -m flask db upgrade```
7. to run the server ```python -m flask run```

## Note
- You must enable email service for the app to run properly as user creation requires email feature to be active.  
- Elasticsearch is must to enable search feature. Otherwise you have to manually remove the elasticsearch feature from all endpoints i.e. models, views and controllers.  
- RedisQueue is must to enable "export all posts" feature.  
- After turning on redis server, start redis queue worker using following command:
    ```
    rq worker microblog-tasks 
    ```
- There can be multiple workers processing the same queue.