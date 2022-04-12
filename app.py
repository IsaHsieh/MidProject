import re
from time import sleep
from typing_extensions import Self
from flask import Flask, request, template_rendered
from flask import url_for, redirect, flash
from flask import render_template
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
from numpy import identity, product
import random, string
from sqlalchemy import null
import cx_Oracle
cx_Oracle.init_oracle_client(lib_dir="/Users/marco/instantclient_19_8") # Marco's init Oracle instant client 位置
# cx_Oracle.init_oracle_client(lib_dir="C:/Users/Isa/instantclient_21_3") # Isa's init Oracle instant client 位置
db = connection = cx_Oracle.connect('group2', 'group22', cx_Oracle.makedsn('140.117.69.58', 1521, 'orcl')) # 連線資訊
cursor = connection.cursor()
print(db.version)
## Flask-Login : 確保未登入者不能使用系統
app = Flask(__name__)
app.secret_key = 'sgdheewetwggsdfsdfsdgdf'  
login_manager = LoginManager(app)
login_manager.login_view = 'login' # 假如沒有登入的話，要登入會導入 login 這個頁面

class User(UserMixin):
    
    pass

@login_manager.user_loader
def user_loader(userid): 
    print("sss:"+userid) 
    user = User()
    user.id = userid
    sql = 'SELECT IDEN, EMAIL FROM USER2 WHERE EMAIL =' + '\''+ userid + '\''
    cursor.execute(sql)
    data = cursor.fetchone()
    user.role = data[0]
    user.name = data[1]
    return user 

# 主畫面
@app.route('/')
def index():
    return render_template('index.html')

# 登入頁面
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':

        account = request.form['account']
        password = request.form['password']

        # 查詢看看有沒有這個資料
        sql = 'SELECT UID2 , UPASSWORD, EMAIL, IDEN , PHONE FROM USER2 WHERE EMAIL =' + '\''+ account + '\''
        print(sql)
        cursor.execute(sql)
        # cursor.prepare('SELECT UID2, EMAIL, PHONE FROM USER2 WHERE EMAIL = :id')
        # cursor.execute(None, {'id': account})

        data = cursor.fetchall() # 抓去這個帳號的資料

        # 但是可能他輸入的是沒有的，所以下面我們 try 看看抓不抓得到
        try:
            DB_password = data[0][1] # true password
            print(DB_password)
            user_id = data[0][2] # user_id
            print(user_id)
            identity = data[0][3] # user or manager
            print(identity)
        # 抓不到的話 flash message '沒有此帳號' 給頁面
        except:
            flash('*沒有此帳號')
            return redirect(url_for('login'))

        if( DB_password == password ):
            user = User()
            user.id = user_id
            login_user(user)

            if( identity == 'user'):
                return redirect(url_for('bookstore'))
            else:
                return redirect(url_for('manager'))
        
        # 假如密碼不符合 則會 flash message '密碼錯誤' 給頁面
        else:
            flash('*密碼錯誤，請再試一次')
            return redirect(url_for('login'))

    
    return render_template('login.html')

# 註冊頁面
@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        user_email = request.form['username']
        user_password = request.form['account']
        user_phone = request.form['password']
        user_identity = request.form['identity']
        
        # 抓取所有的會員帳號，因為下面要比對是否已經有這個帳號
        check_account =""" SELECT EMAIL FROM USER2 """
        cursor.execute(check_account)
        exist_account = cursor.fetchall()
        account_list = []
        for i in exist_account:
            account_list.append(i[0])

        if(user_email in account_list):
            # 如果已經有這個帳號，就會給一個 flash message : 上面會顯示已經有這個帳號了
            flash('Falid!')
            return redirect(url_for('register'))
        else:
            # 在 SQL 裡有設定 member id 是 auto increment 所以第一個值給：null
            # 可參考的設定連結：https://www.abu.tw/2008/06/oracle-autoincrement.html
            sql = 'SELECT UID2 FROM USER2 Order by UID2  desc'
            cursor.execute(sql)
            uid = cursor.fetchone()[0]
            uid = int(uid) +1
            uid2 = str(uid).zfill(3)
            print(uid2)
            sql = 'INSERT INTO USER2 VALUES (' + '\'' + uid2 + '\'' + ',' + '\''+ user_email +'\'' + ',' + '\'' + user_password + '\'' + ',' + '\'' + user_phone + '\'' + ',' + '\'' + user_identity + '\'' + ')'
            print(sql)
            cursor.execute(sql)
            connection.commit()
            return redirect(url_for('login'))

    return render_template('register.html')

# 書店內部
@app.route('/bookstore', methods=['GET', 'POST'])
@login_required # 使用者登入後才可以看
def bookstore():

    # 以防管理者誤闖
    if request.method == 'GET':
        if( current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager'))

    # 查看書本的詳細資料（假如有收到 hid 的 request）
    if 'hid' in request.args:
        hid = request.args['hid']

        # 查詢這本書的詳細資訊
        cursor.prepare('SELECT * FROM HOTEL WHERE HID = :id ')
        cursor.execute(None, {'id': hid})

        data = cursor.fetchone() 
        pname = data[1]
        price = data[2]
        category = data[3]

        product = {
            '商品編號': hid,
            '商品名稱': pname,
            '單價': price,
            '類別': category
        }

        # 把抓到的資料用 json 格式傳給 projuct.html 
        return render_template('product.html', data = product)

    # 沒有收到 hid 的 request 的話，代表只是要看所有的書
    sql = 'SELECT * FROM HOTEL'
    cursor.execute(sql)
    book_row = cursor.fetchall()
    book_data = []
    for i in book_row:
        book = {
            '商品編號': i[0],
            '商品名稱': i[1]
        }
        book_data.append(book)

    # 抓取所有書的資料 用一個 List 包 Json 格式，在 html 裡可以用 for loop 呼叫
    return render_template('bookstore.html', book_data=book_data, user=current_user.name)

# 會員購物車
@app.route('/cart', methods=['GET', 'POST'])
@login_required # 使用者登入後才可以看
def cart():

    # 以防管理者誤闖
    if request.method == 'GET':
        if( current_user.role == 'manager'):
            flash('No permission')
            return redirect(url_for('manager'))

    # 回傳有 hid 代表要 加商品
    if request.method == 'POST':
        
        if "hid" in request.form :
            product_data = add_product()

        elif "delete" in request.form :
            hid = request.values.get('delete')
            user_id = current_user.id #找到現在使用者是誰
            sql = 'SELECT * FROM CART WHERE EMAIL =' + '\'' +user_id + '\''
            cursor.execute(sql)
            tno = cursor.fetchone()[2] # 交易編號
   
            sql  = 'DELETE FROM RECORD WHERE TNO =' + '\'' + tno + '\'' + ' and ' + 'HID = ' + '\''+ hid + '\''
            print('7:'+sql)
            cursor.execute(sql)
            connection.commit() # 把這個刪掉

            product_data = only_cart()
        
        # 點選繼續購物
        elif "user_edit" in request.form:
            change_order()
                
            return redirect(url_for('bookstore'))
        
        elif "buy" in request.form:

            change_order()

            return redirect(url_for('order'))

        elif "order" in request.form:

            user_id = current_user.id #找到現在使用者是誰
            sql = 'SELECT * FROM CART WHERE EMAIL =' + user_id
            cursor.execute(sql)
            tno = cursor.fetchone()[2] # 交易編號

            cursor.prepare('SELECT SUM(TOTAL) FROM RECORD WHERE TNO=:tno ')
            cursor.execute(None, {'tno': tno})
            total = cursor.fetchone()[0] # 總金額
            sql = 'DELETE FROM CART WHERE EMAIL = '+user_id
            cursor.execute(sql)
            connection.commit() # 把這個刪掉

            time = str(datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
            format = 'yyyy/mm/dd hh24:mi:ss'

            cursor.prepare('INSERT INTO ORDER_LIST VALUES ( order2_seq.nextval , :mid, TO_DATE( :time, :format ), :total)')
            cursor.execute(None, {'mid': user_id, 'time':time, 'total':total, 'format':format})
            connection.commit() # 把這個刪掉

            return render_template('complete.html')

    
    product_data = only_cart()
    
    if product_data == 0:
        return render_template('empty.html')
    else:
        return render_template('cart.html', data=product_data)

def add_product():
    user_id = current_user.id #找到現在使用者是誰
    sql = 'SELECT * FROM CART WHERE EMAIL =' + '\''+ user_id + '\''
    cursor.execute(sql)
    data = cursor.fetchone()
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if( data == None): #假如購物車裡面沒有他的資料
        random1 = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        
        sql = 'INSERT INTO CART VALUES (' + '\'' + user_id + '\'' +  ',' + '\'' + time + '\'' + ',' + '\'' + random1 + '\'' ')'
        print(sql)
        cursor.execute(sql)
        connection.commit()
        sql = 'SELECT * FROM CART WHERE EMAIL =' + '\'' +user_id +'\''
        cursor.execute(sql)
        data = cursor.fetchone()
    
    tno = data[2] # 使用者有購物車了，購物車的交易編號是什麼
    hid = request.values.get('hid') # 使用者想要購買的東西
    sql = 'SELECT * FROM RECORD WHERE EMAIL =' +'\''+user_id + '\''+  ' and ' + 'TNO = ' + '\'' + tno +'\''
    print("2:"+sql)
    cursor.execute(sql)
    product = cursor.fetchone()    

    sql = 'SELECT UID2 FROM USER2 WHERE EMAIL = ' +'\''+ user_id +'\''
    print(sql)
    cursor.execute(sql)
    uid3 = cursor.fetchone()[0]    
    print(uid3)
    sql = 'SELECT PRICE FROM HOTEL WHERE hid = ' +'\''+ hid +'\''
    print("3:"+sql)
    cursor.execute(sql)
    price = cursor.fetchone()[0]
    one = '1'
    # 如果購物車裡面沒有的話 把他加一個進去
    if(product == None):
        sql = 'INSERT INTO RECORD VALUES (' + '\''+ user_id + '\'' +','+ '\'' + price +'\''+ ',' + '\''+ tno  + '\''+ ' , '+ '\''+ hid + '\'' + ' , ' + '\''+ one + '\'' + ' , ' + '\''+ uid3 + '\'' +  ' , ' + '\'' + str(time) + '\'' +  ')'
        print("4:"+sql)
        cursor.execute(sql)
        connection.commit()

    else:
        cursor.prepare('SELECT AMOUNT FROM RECORD WHERE TNO = :id and HID=:hid')
        cursor.execute(None, {'id': tno, 'hid':hid})
        print(tno)
        print(hid)
        data = cursor.fetchall()
        print(len(data))
        if len(data) == 0:
            
            print("沒資料")
            sql = 'INSERT INTO RECORD VALUES (' + '\''+ user_id + '\'' +','+ '\'' + price +'\''+ ',' + '\''+ tno  + '\''+ ' , '+ '\''+ hid + '\'' + ' , ' + '\''+ one + '\'' + ' , ' + '\''+ uid3 + '\'' +  ' , ' + '\'' + str(time) + '\'' +  ')'
           
            print("11:"+sql)
            cursor.execute(sql)
            connection.commit()
        else: 
            cursor.prepare('SELECT AMOUNT FROM RECORD WHERE TNO = :id and HID=:hid')
            cursor.execute(None, {'id': tno, 'hid':hid})
            amount = cursor.fetchone()[0]
            print("有資料") 
            cursor.prepare('UPDATE RECORD SET AMOUNT=:amount WHERE hid=:hid and TNO=:tno')
            cursor.execute(None, {'amount':amount+1, 'tno':tno , 'hid':hid})
    
    sql = 'SELECT * FROM RECORD WHERE TNO = '+ '\''+ tno +'\''
    print("5:"+sql)
    cursor.execute(sql)
    product_row = cursor.fetchall()
    print(product_row)
    product_data = []
    for i in product_row:
        sql = 'SELECT HNAME FROM HOTEL WHERE HID =' + '\''+ i[3] + '\''
        cursor.execute(sql)
        price = cursor.fetchone()[0]    
        product = {
            '商品編號': i[3],
            '商品名稱': price,
            '商品價格': i[1],
            '數量': i[2]
        }
        product_data.append(product)
    
    return product_data

def change_order():

    user_id = current_user.id #找到現在使用者是誰
    sql = 'SELECT * FROM CART WHERE EMAIL =' + '\'' + user_id + '\''
    cursor.execute(sql)
    data = cursor.fetchone()

    tno = data[2] # 使用者有購物車了，購物車的交易編號是什麼

    print ("tno:"+tno)
    sql = 'SELECT * FROM RECORD WHERE TNO =' + '\'' + tno + '\''
    cursor.execute(sql)
    product_row = cursor.fetchall()
    print(product_row)
    # for i in product_row:
        
    #     # i[0]：交易編號 / i[1]：商品編號 / i[2]：數量 / i[3]：價格
    #     if int(request.form[i[1]]) != i[2]:
    #         cursor.prepare('UPDATE RECORD SET AMOUNT=:amount, TOTAL=:total WHERE hid=:hid and TNO=:tno')
    #         cursor.execute(None, {'amount':request.form[i[1]], 'hid':i[1], 'tno':tno, 'total':int(request.form[i[1]])*int(i[3])})
    #         connection.commit()
    #         print('change')

    # return 0


def only_cart():
    user_id = current_user.id #找到現在使用者是誰
    sql = 'SELECT * FROM CART WHERE EMAIL =' + '\''+user_id + '\''
    cursor.execute(sql)
    data = cursor.fetchone()

    if( data == None): #假如購物車裡面沒有他的資料
        
        return 0
    

    tno = data[2] # 使用者有購物車了，購物車的交易編號是什麼
    sql = 'SELECT * FROM RECORD WHERE TNO =' +'\''+ tno +'\''
    print("1:"+sql)
    cursor.execute(sql)
    product_row = cursor.fetchall()
    product_data = []
    print(product_row)
    for i in product_row:
        print("qqqqq:"+i[3])
        sql = 'SELECT HNAME FROM HOTEL WHERE HID =' + '\'' + i[3] + '\''
        print("6:"+ sql)
        cursor.execute(sql)
        NAME = cursor.fetchone()[0] 
        product = {
            '商品編號': i[3],
            '商品名稱': NAME,
            '商品價格': i[1],
            '數量': i[4]
        }
        product_data.append(product)
    
    return product_data

@app.route('/manager', methods=['GET', 'POST'])
@login_required
def manager():
    
    if request.method == 'GET':
        if( current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('bookstore'))

    if 'delete' in request.values: #要刪除

        hid = request.values.get('delete')
        print("刪除刪除刪除刪除刪除刪除")
        # 看看 RECORD 裡面有沒有需要這筆產品的資料
        cursor.prepare('SELECT * FROM RECORD WHERE hid=:hid')
        cursor.execute(None, {'hid':hid})
        data = cursor.fetchone() #可以抓一筆就好了，假如有的話就不能刪除
        
        if(data != None):
            flash('faild')
        else:
            cursor.prepare('DELETE FROM HOTEL WHERE hid = :id ')
            cursor.execute(None, {'id': hid})
            connection.commit() # 把這個刪掉

    elif 'edit' in request.values: #要修改
            hid = request.values.get('edit')
            return redirect(url_for('edit', hid=hid))

    book_data = book()

    return render_template('manager.html', book_data=book_data, user=current_user.name)

def book():
    sql = 'SELECT * FROM HOTEL'
    cursor.execute(sql)
    book_row = cursor.fetchall()
    book_data = []
    for i in book_row:
        book = {
            '商品編號': i[0],
            '商品名稱': i[1],
            '商品售價': i[2],
            '商品類別': i[3]
        }
        book_data.append(book)
    return book_data

@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():

    # 以防使用者使用管理員功能
    if request.method == 'GET':
        if( current_user.role == 'user'):
            flash('No permission')
            return redirect(url_for('bookstore'))

    if request.method == 'POST':
        hid = request.values.get('hid')
        new_name = request.values.get('name')
        new_address = request.values.get('address')
        new_price = request.values.get('price')
        new_category = request.values.get('category')
        cursor.prepare('UPDATE HOTEL SET HNAME=:name,HADD=:address, PRICE=:price, HDEC=:category WHERE hid=:hid')
        cursor.execute(None, {'name':new_name, 'address':new_address, 'price':new_price,'category':new_category, 'hid':hid})
        connection.commit()
        
        return redirect(url_for('manager'))

    else:
        product = show_info()
        return render_template('edit.html', data=product)


def show_info():
    hid = request.args['hid']
    cursor.prepare('SELECT * FROM HOTEL WHERE hid = :id ')
    cursor.execute(None, {'id': hid})

    data = cursor.fetchone() #password
    pname = data[1]
    address = data[2]
    price = data[6]
    category = data[3]

    product = {
        '商品編號': hid,
        '商品名稱': pname,
        '地點': address,
        '單價': price,
        '類別': category
    }
    return product

@app.route('/add', methods=['GET', 'POST'])
def add():

    if request.method == 'POST':
    
        cursor.prepare('SELECT * FROM HOTEL WHERE hid=:hid')
        data = ""

        while ( data != None): #裡面沒有才跳出回圈

            number = str(random.randrange( 10000, 99999))
            hid = 'h' + number #隨機編號
            cursor.execute(None, {'hid':hid})
            data = cursor.fetchone()

        name = request.values.get('name')
        address = request.values.get('address')
        price = request.values.get('price')
        category = request.values.get('category')
        platform = request.values.get('platform')

        if ( len(name) < 1 or len(price) < 1): #使用者沒有輸入
            return redirect(url_for('manager'))
        cursor.prepare('INSERT INTO HOTEL VALUES (:hid, :name, :address, :category , :location , :platform, :price )')
        cursor.execute(None, {'hid': hid, 'name':name, 'address': address , 'category':category , 'location':address, 'platform':platform , 'price':price })
        connection.commit()

        return redirect(url_for('manager'))

    return render_template('add.html')

@app.route('/order')
def order():

    user_id = current_user.id #找到現在使用者是誰
    cursor.prepare('SELECT * FROM CART WHERE EMAIL = :id ')
    cursor.execute(None, {'id': user_id})
    data = cursor.fetchone()
    
    tno = data[2] # 使用者有購物車了，購物車的交易編號是什麼

    sql = 'SELECT * FROM RECORD WHERE TNO = '+ tno + '\''
    cursor.execute(sql)
    product_row = cursor.fetchall()
    product_data = []

    for i in product_row:
        sql = 'SELECT PNAME FROM HOTEL WHERE hid =' + i[1]
        cursor.execute(sql)
        price = cursor.fetchone()[0] 
        product = {
            '商品編號': i[1],
            '商品名稱': price,
            '商品價格': i[3],
            '數量': i[2]
        }
        product_data.append(product)
    
    cursor.prepare('SELECT SUM(TOTAL) FROM RECORD WHERE TNO = :id')
    cursor.execute(None, {'id': tno})
    total = cursor.fetchone()[0]

    return render_template('order.html', data=product_data, total=total)

@app.route('/dashboard')
@login_required
def dashboard():
    revenue = []
    namelist = []
    cursor.prepare('SELECT HID , HNAME FROM HOTEL')
    cursor.execute(None)
    row = cursor.fetchall()
    for i in range(len(row)):
        namelist.append(row[i][1])
        sql = 'SELECT SUM(AMOUNT) FROM RECORD WHERE HID=' + '\'' +row[i][0] + '\''
        cursor.execute(sql)
        wow = cursor.fetchone()
        if wow[0] == None:
            revenue.append(0)
        else:
            revenue.append(wow[0])
    return render_template('dashboard.html',  revenue = revenue  ,  namelist = namelist)

@app.route('/logout')  
def logout():

    logout_user()  
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.debug = True #easy to debug
    app.secret_key = "sgdheewetwggsdfsdfsdgdf"
    app.run()