import datetime as dt
from peewee import *
import telebot
from conf import *


db = SqliteDatabase('baza.db')

bot = telebot.TeleBot(
    api_key, parse_mode="HTML")


class BaseModel(Model):
    """Bazowy model umożliwiający połączenie obiektów z bazą danych przy użyciu Peewee."""
    class Meta:
        database = db


class User(BaseModel):
    """Reprezentuje pojedynczego użytkownika aplikacji Telegram.

    telegram_id -- ID użytkownika Telegrama
    """
    telegram_id = IntegerField()


class Tag(BaseModel):
    """Reprezentuje tag którym można oznaczyć istniejące zadania.

    name -- nazwa tagu
    user -- użytkownik, do którego tag należy
    """
    name = CharField()
    user = ForeignKeyField(User, backref='tags')


class TaskList(BaseModel):
    """Reprezentuje listę zadań.

    name -- nazwa listy zadań
    user -- użytkownik, do którego lista należy
    """
    name = CharField()
    user = ForeignKeyField(User, backref='tasklists')

    def add_task(self, task):
        """Przypisuje podane zadanie do listy."""
        task.tasklist = self
        task.save()


class Task(BaseModel):
    """Reprezentuje pojedyncze zadanie do wykonania.

    name -- treść zadania
    estimated_time -- szacowany czas potrzebny na wykonanie zadania w sekundach
    tasklist -- lista zadań do której zadanie należy (jeżeli do jakiejś należy)
    user -- użytkownik, do którego lista należy                                   
    """
    name = CharField()
    estimated_time = IntegerField()
    tasklist = ForeignKeyField(TaskList, backref='tasks', null=True)
    user = ForeignKeyField(User, backref='tasks')

    @staticmethod
    def get_task(user, id):
        """Zwraca zadanie o podanym `id` jeżeli należy do podanego użytkownika. W przeciwnym razie zwraca None."""
        task = Task.get_by_id(id)
        if task.user.id == user.id:
            return task
        else:
            return None

    def set_est_time(self, minutes):
        """Ustawia szacowany czas wykonania zadania (w minutach)."""
        self.estimated_time = int(minutes*60)
        self.save()

    def add_tag(self, tag):
        """Dodaje tag do zadania."""
        tasktag = TagTask(task=self, tag=tag)
        tasktag.save()

    def remove_tag(self, tag):
        """Usuwa tag z zadania."""
        a = TagTask.delete().where((TagTask.task_id == self.id) &
                                   (TagTask.tag_id == tag.id))
        a.execute()

    @staticmethod
    def get_by_tag(user, tag_name):
        """Zwraca listę zadań należących do użytkownika przypisanych do zadanego tagu."""
        return ((Task.select()
                 .join(TagTask)
                 .join(Tag)
                 .where((Tag.name == tag_name) & (Tag.user == user))))

    @staticmethod
    def get_by_plan(user, plan_date):
        """Zwraca listę zadań należących do użytkownika przypisanych do danego planu."""
        return ((Task.select()
                 .join(TaskPlan)
                 .join(Plan)
                 .where((Plan.date == plan_date) & (Plan.user == user))))


class TagTask(BaseModel):
    """Reprezentuje powiązanie pomiędzy klasami `Tag` i `Task`"""
    tag = ForeignKeyField(Tag)
    task = ForeignKeyField(Task)


# class Pomidor(BaseModel):
#     duration = None
#     start = DateField()
#     user = ForeignKeyField(User, backref='pomidori')

#     def change_duration(self, time):
#         pass


class Plan(BaseModel):
    """Przechowuje listę zadań zaplanowanych na dany termin.

    date -- termin wykonania zadań
    user -- właściciel planu
    """
    date = DateField()
    user = ForeignKeyField(User, backref='plans')

    def add_task(self, task):
        """Dodaje zadanie do planu."""
        taskplan = TaskPlan(task=task, plan=self)
        taskplan.save()

    def remove_task(self, task):
        """Usuwa zadanie z planu."""
        a = TaskPlan.delete().where((TaskPlan.plan == self) &
                                    (TaskPlan.task == task))
        a.execute()


class TaskPlan(BaseModel):
    """Reprezentuje powiązanie pomiędzy klasami `Task` i `Plan`."""
    plan = ForeignKeyField(Plan)
    task = ForeignKeyField(Task)


# class Statistic():
#     def __init__(self, start, dur):
#         start = dt.date(start)
#         duration = dt.timedelta(days=dur)
#         tasks_done = None
#         mean_time_per_day = None
#         time_per_tag = None


db.connect()
db.create_tables([Tag, Task, TagTask, Plan, TaskPlan, User, TaskList])


@bot.message_handler(commands=['start'])
def send_welcome(message):
    """Odpowiada na komendę /start, która rozpoczyna interakcję z botem na Telegramie."""
    bot.reply_to(
        message, """
Do używania tego bota przydadzą Ci się komendy:

<i>argumenty do wprowadzenia przez użytkownika:
&lt;argument&gt; - parametr wymagany 
[argument] - parametr opcjonalny</i>

<b>List all Tasks/List by Tag</b>
/list <i>[nazwa tagu]</i> - wyświetla wszystkie Tasks użytkownika/ [wyświetla wszystkie Tasks które mają przypisany Tag]

<b>Edit Tasks</b>
/task <i>[szacowany czas] &lt;nazwa zadania&gt;</i> - tworzy nowy Task o podanej nazwie [dodaje do Task szacowany czas wykonania go]
/est <i>&lt;szacowany czas&gt; &lt;numer zadania&gt;</i> - dodaje do Task szacowany czas wykonania go
/delete <i>&lt;numer zadania&gt;</i> - usuwa Task o podanym numerze

<b>Edit Tags</b>
/tag <i>&lt;numer zadania&gt; &lt;nazwa tagu&gt;</i> - dodaje Tag do Task
/untag <i>&lt;numer zadania&gt; &lt;nazwa tagu&gt;</i> - usuwa Tag z Task

<b>Edit TaskLists</b>
/addtolist <i>&lt;numer zadania&gt; &lt;nazwa tasklisty&gt;</i> - dodaje Task do TaskListy
/tasklist <i>&lt;nazwa tasklisty&gt;</i> - wyświetla Tasks z TaskList o podanej nazwie
/removefromlist <i>&lt;numer zadania&gt;</i> - usuwa Task z TaskListy

<b>Edit Plans</b>
/plan <i>&lt;data w formacie YYYY-MM-DD&gt; [numer<b>y</b> zadań]</i> - pokazuje Plan na dany dzień [dodaje Tasks do Plan danego dnia]
/unplan <i>&lt;data w formacie YYYY-MM-DD&gt; [numer<b>y</b> zadań]</i> - usuwa Tasks z Plan na dany dzień
""")


@bot.message_handler(commands=['task'])
def create_todo(message):
    """Implementuje komendę /task, pozwalącą na dodawanie tasków."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, *args = message.text.split()
    if len(args) == 0:
        bot.reply_to(
            message, "Usage: /task [estimated time in min] &lt;your task&gt;")
        return
    est = 0
    text = ''
    try:
        est = int(args[0])
        text = " ".join(args[1:])
    except ValueError:
        text = ' '.join(args)
    todo = Task(user=user, name=text)
    todo.set_est_time(est)
    bot.reply_to(message, "Task saved.")


@bot.message_handler(commands=['est'])
def estimate(message):
    """Implementuje komendę /est, pozwalającą na szacowanie czasu potrzebnego na wykonanie zadania."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, *args = message.text.split()
    if len(args) == 0:
        bot.reply_to(
            message, "Usage: /est &lt;estimated time in min&gt; &lt;task number&gt;")
        return
    est = int(args[0])
    num = int(args[1])
    Task.get_task(user, num).set_est_time(est)


@bot.message_handler(commands=['list'])
def list_todos(message):
    """Implementuje komendę /list, pozwalającą na wylistowanie wszystkich zadań lub przypisanych do danego tagu."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    args = message.text.split(" ")
    todos = []
    if len(args) == 1:
        todos = Task.select().where(Task.user == user)
    else:
        todos = Task.get_by_tag(user, args[1])
    msg = "Your Tasks:\n"
    for todo in todos:
        est = todo.estimated_time/60
        msg += f"{todo.id}. {todo.name} <i>({est}m)</i>\n"
    bot.reply_to(message, msg)


@bot.message_handler(commands=['tag'])
def tag_task(message):
    """Implementuje komendę /tag, pozwalającą na tagowanie zadań."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, num, name = message.text.split(" ", 2)
    tag, _ = Tag.get_or_create(user=user, name=name)
    task = Task.get_task(user, num)
    task.add_tag(tag)
    bot.reply_to(message, "Tag added to task.")


@bot.message_handler(commands=['untag'])
def untag(message):
    """Implementuje komendę /untag, pozwalającą na usuwanie tagów z zadań."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, num, name = message.text.split(" ", 2)
    tag = Tag.get(user=user, name=name)
    task = Task.get_task(user, num)
    task.remove_tag(tag)
    bot.reply_to(message, "Tag removed from task.")


@bot.message_handler(commands=['tasklist'])
def set_tasklist(message):
    """Implementuje komendę /tasklist, pozwalającą na listowanie zadań w liście."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, name = message.text.split(" ", 1)
    tasklist = TaskList.get(user=user, name=name)
    msg = f"Tasklist \"{name}\":\n"
    for todo in tasklist.tasks:
        est = todo.estimated_time/60
        msg += f"{todo.id}. {todo.name} <i>({est}m)</i>\n"
    bot.reply_to(message, msg)


@bot.message_handler(commands=['addtolist'])
def addtolist(message):
    """Implementuje komendę /addtolist, pozwalającą na przypisywanie zadań do list."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, num, name = message.text.split(" ", 2)
    tasklist, _ = TaskList.get_or_create(user=user, name=name)
    todo = Task.get_task(user, num)
    tasklist.add_task(todo)
    bot.reply_to(message, "Task added to tasklist.")


@bot.message_handler(commands=['removefromlist'])
def removefromlist(message):
    """Implementuje komendę /removefromlist, pozwalającą na usuwanie zadań z list."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    _, num = message.text.split(" ", 1)
    todo = Task.get_task(user, num)
    todo.tasklist = None
    todo.save()
    bot.reply_to(message, "Task removed from tasklist.")


@bot.message_handler(commands=['delete'])
def delete(message):
    """Implementuje komendę /delete, pozwalającą na usuwanie zadań."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    split = message.text.split(" ")
    if len(split) != 2:
        bot.reply_to(message, "Usage: /delete &lt;task number&gt;")
        return
    todo_id = int(split[1])
    todo = Task.get_task(user, todo_id)
    todo.delete_instance()
    bot.reply_to(message, "Deleted.")


@bot.message_handler(commands=['lisy'])
def lisy(message):
    """Implementuje komendę /lisy, wysyłającą obrazek z dwoma lisami."""
    with open('lisy.png', 'rb') as file:
        bot.send_photo(message.chat.id, file)


@bot.message_handler(commands=['plan'])
def planning(message):
    """Implementuje komendę /plan, pozwalającą na dodawanie zadań do planów."""
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    # date format: YYYY-MM-DD
    # /plan date tasks.ids
    split = message.text.split(" ")
    date = dt.datetime.strptime(split[1], "%Y-%m-%d")
    msg = f"Plan for {split[1]}:\n"
    if len(split) == 2:
        todos = Task.get_by_plan(user, date)
        total_est = 0
        for todo in todos:
            est = todo.estimated_time/60
            total_est += est
            msg += f"{todo.id}. {todo.name} <i>({est} m)</i>\n"
        msg += f"Estimated time for <b>{date.strftime('%Y-%m-%d')}</b>: <i>{total_est} m</i>"
        bot.reply_to(message, msg)
    else:
        plan, _ = Plan.get_or_create(user=user, date=date)
        for arg in split[2:]:
            try:
                num = int(arg)
                task = Task.get_task(user, num)
                if task is None:
                    continue
                plan.add_task(task)
            except ValueError:
                pass
        bot.reply_to(
            message, f"Plan for <b>{date.strftime('%Y-%m-%d')}</b> updated.")


@bot.message_handler(commands=['unplan'])
def unplantask(message):
    """Implementuje komendę /unplan, pozwalającą na usuwanie zadań z planów."""
    # date format: YYYY-MM-DD
    # /unplan date tasks.ids
    user, _ = User.get_or_create(telegram_id=message.from_user.id)
    split = message.text.split(" ")
    date = dt.datetime.strptime(split[1], "%Y-%m-%d")
    msg = f"Plan for {split[1]}:\n"
    plan, _ = Plan.get_or_create(user=user, date=date)
    for arg in split[2:]:
        try:
            num = int(arg)
            task = Task.get_task(user, num)
            if task is None:
                continue
            plan.remove_task(task)
        except:
            pass
    bot.reply_to(
        message, f"Plan for <b>{date.strftime('%Y-%m-%d')}</b> updated.")


# uruchamia bota
bot.polling()
