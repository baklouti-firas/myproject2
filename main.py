
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import time

app = FastAPI()

def get_db_conn():
    while True:
        try:
            conn = psycopg2.connect(
                host='db',  # Utilisez le nom du service Docker
                database='fastapic',
                user='postgres',
                password='firas',
                cursor_factory=RealDictCursor
            )
            print("Database connection successful!")
            return conn
        except psycopg2.Error as e:
            print("Connection to database failed.")
            print(f"Error: {e}")
            time.sleep(2)

class Task(BaseModel):
    name: str 
    description: Optional[str] = None
    priority: int

@app.get("/tasks/")
def read_tasks(skip: int = 0, limit: int = 10):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM tasks ORDER BY id OFFSET {skip} LIMIT {limit}")
    tasks = cursor.fetchall()
    cursor.close()
    conn.close()
    return tasks

@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
    task = cursor.fetchone()
    cursor.close()
    conn.close()
    if task:
        return task
    raise HTTPException(status_code=404, detail="Task not found")

@app.post("/tasks/", response_model=Task)
def create_task(task: Task):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (name, description, priority) VALUES (%s, %s, %s) RETURNING *",
        (task.name, task.description, task.priority)
    )
    new_task = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return new_task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
        conn.commit()  # Ne pas oublier de valider la transaction
        return {"message": "Task deleted successfully"}
    except Exception as e:
        conn.rollback()  # En cas d'erreur, annuler la transaction
        return {"error": str(e)}, 500
    finally:
        cursor.close()
        conn.close()

@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: Task):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tasks SET name = %s, description = %s, priority = %s WHERE id = %s RETURNING *",
        (task.name, task.description, task.priority, task_id)
    )
    updated_task = cursor.fetchone()
    conn.close()
    cursor.close()
    if updated_task:
        return updated_task
    raise HTTPException(status_code=404, detail="Task not found")