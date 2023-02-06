### 갑분 초대 => 알림 시스템 만들기



#### Invite 분석정리하기



1. employee(current_user)는 특정User에 대해 `[직원전환] -> employee가 입력` 대신 `[직원초대]`를 누르면

   - `employee/invites` route에서
     - current_user -> ~~employee_id~~(`inviter_id`) - > **user_id** 항상 직원->User초대만 있는 것이 아니기 때문에 공용적인 user_id를 넣는다
     - 상대user -> user_id(`invitee_id`)
       - ~~employee~~는 user는 Invite.inviter_id에 대한 one으로서 `.inviters`를 통해, `내가 보낸 초대들`을 볼 수 있다.
       - users는 invite.invitee_id에 대한 one으로서 `.invitees`를 통해, `내가 받은 초대들`을 볼 수 있다.
     - **초대의 주제type  or  상위 주제entity의 id(fk)**
       - ~~ex> employee관련 이므로, employee_id를 넣고 하위의 초대로 만들게 한다~~
       - 검색이나 조회를 위해 `초대들마다 상위주제`가 정해져있어야한다.
         - 특정 예약entity에 대한 초대가 아니므로, 상위entity 없다
     - 까지만 넣고, 내부 deafult값으로 status, answered False로 Invite객체를 만든다

   ```python
   class Inivite
   #class PlayerInvite(db.Model):
       playerinvite_id = db.Column(db.Integer, primary_key=True)
       # invitees
       guest_id = db.Column(db.Integer, db.ForeignKey('player.player_id'))
       # inviters
       host_id = db.Column(db.Integer, db.ForeignKey('player.player_id'))
       # 상위주제entitye대신 초대 Category Type으로
       #booking_id = db.Column(db.Integer, db.ForeignKey('booking.booking_id'))
   
       status = db.Column(db.Boolean, default=False)
       answered = db.Column(db.Boolean, default=False)
   
   ```

   

   ```python
   guests = db.relationship("PlayerInvite", foreign_keys='PlayerInvite.guest_id')
   
   hosts = db.relationship("PlayerInvite", foreign_keys='PlayerInvite.host_id')
   ```

   

   

   ```python
   @player.route('/players/invite/add', methods=['POST'])
   @token_required
   def invite_player(current_user):
       data = request.get_json()
       invite = PlayerInvite(guest_id=data['guest_id'],
                             host_id=data['host_id'],
                             booking_id=data['booking_id'])
       db.session.add(invite)
       db.session.flush()
       db.session.commit()
       return {'message': 'Success!'}
   ```

   



2. employee가 `[직원초대]`를 누르면  초대 뿐만 아니라 **notification이 해당 user에게 가야할 것**이다.



3. 초대받은 user는 notification을받아 -> `메세지`상의 `[직원 초대 수락]` 를 클릭할 것이다



4. 아직, notification이 없으면, 바로 `[내가 받은 초대]`를 클릭하여 초대 목록을 확인한다

   - /auth/userinfo(내 정보) 다음 칸의 `/auth/invite/invitee`(내가 **받은(invitee)** 초대)에서 확인한다
     - 내가 받은 초대 tab은   user.invitees로서, 데이터가 잇을때만 나타나게 해야, 일반회원들한테 혼란을 줄일 수 있을 것이다?

   ```python
   def my_invites(user_id):
       player = Player.query.filter_by(user_id=user_id).first()
       invites = PlayerInvite.query.filter_by(guest_id=player.player_id)
   ```

   ```python
   @player.route('/players/invites/guest', methods=['GET'])
   @token_required
   def get_my_invites(current_user):  # Return invites sent to the logged player.
   
       output = []
   
       for invite in my_invites(current_user.id):
   
           invite_data = {'booking_id': invite.booking_id,
                          'spot_name': invite.spot_name,
                          'spot_id': invite.spot_id,
                          'status': invite.status,
                          'invite_id': invite.playerinvite_id,
                          'guest_id': invite.guest_id,
                          'host_name': f'{invite.host_name} {invite.host_surname}'
                          }
           output.append(invite_data)
   
       return {'invites': output}
   ```

   

5. 받은 초대목록 중에 `[초대거부/초대승락]`을 선택해서 누른다

   - 초대 수락

     - 초대는 employee/invite/add지만 
     - 초대수락은 `auth/invite/accept`로 받는다.
       - 초대id로 해당 초대객체를 가져와서 default False였던 **status(수락여부)와 answered(응답여부)를  True**로 놓는다.
     - **초대수락시, 상위entity에 하위entity로서 구성원들을 LineUp entity 모을 수 있지만, 여기선 해당 초대에 대한 상위entity (X), 주제Type에 수락자들을 모을 필요가 없다**
     - **초대 수락시, `employee/add form으로 rediect`해야할 것 같다**

     ```python
     @player.route('/players/invites/accept', methods=['POST'])
     @token_required
     def accept_invite(current_user):
         data = request.get_json()
         invite = PlayerInvite.query.filter_by(playerinvite_id=data['playerinvite_id']).first()
         invite.status = True
         invite.answered = True
         
         db.session.add(invite)
         
         #lineup = Lineup(player_id=data['player_id'],
                    #     booking_id=data['booking_id'])
         
         #db.session.add(lineup)
         db.session.commit()
         return {'message': 'Success!'}
     ```

   - **초대 거부는 invite에서 데이터를 삭제**한다

   - 그렇다면

     - 초대수락 route가 아니라 초대 answer_invite route로 만들고
       - `초대 수락`시 ->  Employeeform + **초대자의 role미만으로 선role선택가능하도록 동적필드choices** 로 `초대Type에 맞는 redirect `-> 초대 삭제 -> **render_tempalte(새로 route파서)**
       - `초대 거부`시 -> 초대 삭제
     - **그렇다면, 초대Type은 value로 초대수락시 `redirect될 url or render될 form과 template?`을 가져야한다? **
       - 초대Type에 다른 redirect_url을 어디다가 기입할까? IntEnum은 int만 저장하는데?
       - route에서 if 초대Type -> redirect_url을 배정해줘야하나?
         - 초대Type + form에 들어갈 정보도 redirect_url에 같이 줘야한다 (furl)
         - 그렇다면, invite에는 복잡한 고유key칼럼을 url대신 소유하고 있다가 **초대Type에 맞는, url을 만들어내는 함수를 소유한다**
     - 현재의 employee/add는 
       - employeeform에는 user_id, g.user( current_employee_id)가
       - route자체적으로는 role.chiefstaff이상이 필요한 상태다
       - 일반 유저도 접속할 수 있는 /auth/invite/employee/add가 필요할 듯하다?

     ```python
         def save(self, **kwargs):
             if not self.pk:
                 self.key = self.generate_key()
     
             return super().save(**kwargs)
     
         @staticmethod
         def generate_key():
             return get_random_string(64).lower()
     
         def send(self, request=None):
             url = self.get_absolute_url()
             if request:
                 url = request.build_absolute_uri(url)
     
             template = find_template("invite")
             context = {
                 "inviter_name": self.inviter.get_full_name(),
                 "email": self.invitee_email,
                 "invite_link": url,
             }
     
             return template.send_email([self.invitee_email], context)
     
         def get_absolute_url(self) -> str:
             return reverse("accounts:invite_accept", kwargs={"key": self.key})
     
         def expired(self) -> bool:
             expiration_date = self.created_on + timedelta(days=settings.INVITE_EXPIRY)
             return expiration_date <= timezone.now()
     ```

6. invite에는 **`create_on`을 넣고, 만료기간도 계산해서, `내가 받은 초대 조회`시 `is_expired도 where`로 걸어야할 것 같다**

7. 직원이라면, 내가 보낸 초대 목록도 확인할 수 있게 하여

   - answered로 응답됬는지
   - status(is_accpeted)로 수락/거부 여부도 볼 수 있게 하면 될 것 같다





### Invite  accept 개발하기

![image-20221221010203006](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221010203006.png)

![image-20221221010210006](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221010210006.png)



![image-20221221024340316](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221024340316.png)



#### 01 초대수락하면, invite_id만 넘겨서 [직원add Form재활용하지만, role이 정해진상태]로 form 작성하는 GET+POST route로 가야한다

- 기존 EmployeeForm은 `admin.employee_add route`에서 기본정보를위한 `user`, role선택을 위한 `g.user -> current_user(직원)`을 인자로 받았다
  - EmployeeForm의 변수를 `user` / `employer`로  변경한다.
- 또한, `employee=` 키워드는, **수정form에서 invitee의 Employee객체를 받아 정보를 미리 입력하는 것**이다.
  - 직원초대시에는 수정이 아니므로 employee=는 넣어줄 필요 없다.
- **문제는, EmployeeForm(직원add)에서의 `role선택 필드만 값을 미리 주고, view에서는  빠져야하는 것`**





##### inviter/invitee_id를 넘기지말고, invite_id만 넘기면 정보가 다들어가있으며, Invite자체도 처리해야한다

```html
<a class="level-item button is-primary is-small"
   href="{{url_for('auth.employee_invite_accept', id=invite.id)}}"
   >
    <span style="margin-right: 1px;" class="icon"><i class="mdi mdi-check"></i></span>
    수락
</a>
```



#### 02 EmployeeForm 수정해서, 직원전환시 employer= / 직원초대 수락시 role=객체를 받아 role을 결정하게 한다

```python
def __init__(self, user,
             employer=None, role=None, # 직원전환시 상사객체 OR 직원초대시, role객체 =>  role을 선택할 수 있거나 role을 미리 채운다
             employee=None, # 수정을 위한 미리생성된 user의 employee객체
             *args, **kwargs):
	#...
    
    # 1) employer=는 직접 [직원전환]버튼을 누른 상태로서, role을 해당 employer 범위안에서 결정한다 
    if employer:
        # 직원전환 상사 [current_user]로 부여할 수 잇는 role을 채운다.
        with DBConnectionHandler() as db:
            #### 직원전환시 USER는 옵션에서 제외해야한다. -> 나보다는 낮지만,  STAFF이상으로 -> where. Role.is_STAFF 추가
            roles_under_current_user = db.session.scalars(
                select(Role)
                .where(Role.is_under(employer.role))
                .where(Role.is_(Roles.STAFF))
            ).all()
            self.role_id.choices = [(role.id, role.name) for role in roles_under_current_user]
            # 2) role=은 [직원초대]를 보낼 때 EmployeeInvite에 담긴 role_id => 해당role 1개만 지정되며 수정불가능하게 비활성화한다. 
            if role:
                #### select는 필드의 값을 미리 채울 때, .data가 아니라 .choices에 tuple1개 list를 1개만 넘기면 된다.
                # cf) view에서는 subfield.data, subfield.label로 쓰임
                self.role_id.choices = [(role.id, role.name)]
                # role의 choie를 1개만 배정해놓고, 더이상 수정 불가능하게 막아주자.
                self.role_id.render_kw = dict(disabled=True)
```



#### 03 route는 Invite속 invitee정보와 role정보를 빼와서 form을 만들고 뿌려준다

```python
@auth_bp.route('/invite/employee/accept/<int:id>/', methods=['GET', 'POST'])
@login_required
def employee_invite_accept(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)
        # 1) 수락했으면, [해당 invite]에서 invitee와, role을 가져와 수정한다
        #  => 모든 정보가 입력되면 is_answered된 상태 & is_accepted 처리까지 해줘야한다.
        # invite.is_answered = True
        # invite.is_accepted = True
        # db.session.add(invite)

        # 2) 수락했으면, invitee인 [User]의 기본정보를 위해  user객체를 구해온다
        invitee_user = db.session.get(User, invite.invitee_id)
        # 3) 수락했으면, invter 정보 대신 role_id로 해당 [Role]을 배정해줘야한다
        role = db.session.get(Role, invite.role_id)

        form = EmployeeForm(invitee_user, role=role)


    return render_template('admin/employee_form.html',
                           form=form)

```

![image-20221221145531745](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221145531745.png)
![image-20221221145546294](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221145546294.png)



#### 04 form은 재활용했더라도, html은 menus 블락이 다르고, 수정완료시 돌아갈 url도 다르기 때문에 [userinfo_employee_form.html]을 새로 만들어준다.



##### 상속용 base_form.html  (default is-10으로 채워진) 생성 + 기본적으로 form error 메세지도 받아야한다(flush는 결과화면이 아니므로안받는다.)

- base기반으로 상속할 때 , `form_title`과 `form`block을 채우면된다. 필요시 `vue_script`등
  - **추가로 default form의 `column_size`를 10으로 해놓고 조절할 수 있게 한다**

- **base의 hero블락을 제거하고, main을 빈자리로 세워놈.**

```html
{% extends 'base.html' %}

{% block hero %} {% endblock hero %}

{% block main %}
<div class="box is-radiusless m-6">
    <div class="columns is-centered">
        <div class="column is-{%- block column_size -%}  10  {%- endblock column_size -%}-fullhd">

            <div class="title has-text-centered">
                {% block form_title %}
                
                {% endblock form_title %}
            </div>

            <!-- form validation -->
            {% if form and form.errors %}
            <b-message type="is-danger">
                <ul class="errors">
                    {% for error, v in form.errors.items() %}
                    <li>{{ error }}：{{ v[0] }}</li>
                    {% endfor %}
                </ul>
            </b-message>
            {% endif %}


            {% block form %}
            
            {% endblock form %}

        </div>
    </div>
</div>
{% endblock main %}

```



##### base_form을 상속하여 자체 form페이지로 user_employee_form.html 생성

- ![image-20221221155131628](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221155131628.png)

  ![image-20221221155140895](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221155140895.png)
  ![image-20221221155204731](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221155204731.png)

  ![image-20221221195317403](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221195317403.png)

```html
{% extends 'base_form.html' %}

{%- block column_size -%} 9 {%- endblock column_size -%}

{% block form_title %} 직원 전환 {% endblock form_title %}


{% block form %}
<form action="" method="post" class="column mt-4" enctype="multipart/form-data">
    {{ form.csrf_token }}
    <!-- 바깥 columns 에 is-multine을 줘야 칼럼이 넘어가면 다음줄로 내린다-->
    <div class="columns is-mobile is-multiline"
         style="border-bottom: #ededed solid 1px; padding-bottom: 1rem">
        <div class="column is-narrow">
            <figure class="image is-96x96">
                <img class="is-rounded" style="height: 100%;"
                     :src="
                         img_file_url ? img_file_url :
                         `
                         {% if form.user.avatar %}
                         {{url_for('download_file', filename=form.user.avatar)}}
                         {% else %}
                         {{url_for('static', filename='/img/user/default_avatar.svg')}}
                         {% endif %}
                         `
                        "
                >
            </figure>
        </div>

        <!-- username -->
        <div class="column is-narrow">
            <div style="padding-top: 1.5rem;">
                <h1 class="title is-size-4">{{ form.user.username }}</h1>
            </div>
        </div>

        <!-- avatar  -->
        <div class="column is-narrow is-7 has-text-centered">
            <div style="padding-top: 1.5rem;">
                <!-- 버튼 가운데정렬은, flex가 되는 b-field태그의 class로 주면 된다. -->
                <b-field class="file is-primary is-justify-content-center"
                         :class="{'has-name': !!img_file}">
                    <b-upload
                            class="file-label" rounded
                            v-model="img_file"
                            name="avatar"
                    >
                                      <span class="file-cta">
                                        <b-icon class="file-icon" icon="upload"></b-icon>
                                        <span class="file-label">{$ img_file.name || "아바타 사진 업로드" $}</span>
                                      </span>
                    </b-upload>
                </b-field>
            </div>
            <p class="help has-text-grey-light">
                {{ form.avatar.description }}
            </p>
        </div>


    </div>


    <!-- 기본정보: 추가정보였던 정보들을 기본정보로서 form이 필수로 받는다.    -->
    <div class="columns" style="padding:1rem 0; ">
        <div class="column is-2">
            <p>기본 정보</p>
        </div>
        <div class="column">
            <!-- email -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.email.label(class='label')}}</span>
                </div>
                <div class="column is-5">
                    <span class=" has-text-black-ter">{{ form.email(class='input') }}</span>
                    <p class="help has-text-primary-dark">
                        {{ form.email.description }}
                    </p>
                </div>
            </div>

            <!-- sex -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.sex.label(class='label')}}</span>
                </div>
                <div class="column is-narrow">
                    {% for subfield in form.sex %}
                    <input {%if subfield.checked %}checked {% endif %} type="radio"
                           id="{{ subfield.id }}" name="{{ form.sex.id }}"
                           value="{{ subfield.data }}">
                    {{ subfield.label }}
                    {% endfor %}
                </div>
            </div>


            <!-- 전화번호  -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex ">
                    <span class=" has-text-grey-light">{{form.phone.label(class='label')}}</span>
                </div>
                <!--                <div class="column">-->
                <div class="column is-4">
                    <!-- descript이 달린 경우, column에 사이즈를 주지말고, 세부요소에 column + is-   p태그에 column + py-0을 주자-->
                    <span class="has-text-black-ter">{{ form.phone(class='input') }}</span>
                    <!--                    <span class="has-text-black-ter column is-4">{{ form.phone(class='input') }}</span>-->
                    <!--                    <p class="help has-text-primary-dark column py-0">-->
                    <!--                        {{ form.phone.description }}-->
                    <!--                    </p>-->
                </div>

            </div>
            <!-- 주소   -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{ form.address.label(class='label')}}</span>
                </div>
                <div class="column ">
                    <span class=" has-text-black-ter">{{ form.address(class='input') }}</span>
                </div>
            </div>

        </div>
    </div>

    <!-- 직원정보   -->
    <div class="columns" style="padding:1rem 0; ">
        <div class="column is-2">
            <p>직원 정보</p>
        </div>
        <div class="column">
            <!-- name -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.name.label(class='label')}}</span>
                </div>
                <div class="column is-3">
                    <span class="has-text-black-ter">{{ form.name(class='input') }}</span>
                </div>
            </div>

            <!-- sub_name(영어이름) -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.sub_name.label(class='label')}}</span>
                </div>
                <div class="column is-4">
                    <span class=" has-text-black-ter">{{ form.sub_name(class='input') }}</span>
                </div>
            </div>

            <!-- 주민번호   -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex ">
                    <span class=" has-text-grey-light">{{form.birth.label(class='label')}}</span>
                </div>
                <div class="column is-5">
                    <!--                <div class="column">-->
                    <span class="has-text-black-ter">{{ form.birth(class='input') }}</span>
                    <!--                    <span class="has-text-black-ter column is-5">{{ form.birth(class='input') }}</span>-->
                    <!--                    <p class="help has-text-primary-dark column py-0">-->
                    <!--                        {{ form.birth.description }}-->
                    <!--                    </p>-->
                </div>
            </div>

            <!-- 직위  -->
            <div class="columns is-mobile" style="border-bottom: #ededed solid 1px">
                <div class="column is-3 is-align-items-center is-flex">
                    <span class=" has-text-grey-light">{{form.role_id.label(class='label')}}</span>
                </div>
                <div class="column is-4">
                    <div class="select is-half">
                        {{ form.role_id }}
                    </div>
                </div>
            </div>

            <!-- 입사일 -->
            <div class="columns">
                <div class="column is-3">
                    <p>{{ form.join_date.label(class='label')}}</p>
                </div>
                <div class="column is-4 ">
                    <div class="content">
                        <b-field>
                            <b-datepicker
                                    icon="calendar-today"
                                    editable
                                    v-model="date"
                            >
                            </b-datepicker>
                        </b-field>
                        <!-- datefield는 외부에서 값을 받을 땐, 자기고유 format yyyy-m-d 형식의  자기고유타입 string만 받더라. -->
                        {{form.join_date(class='input', type='hidden', **{'v-model':'stringDate'})}}
                    </div>
                </div>
            </div>

        </div>
    </div>


    <div class="columns is-mobile is-centered my-3">
        <div class="column is-narrow">
            <a href="javascript:history.back();"
               class="button is-primary is-light mr-2">
                뒤로가기
            </a>
        </div>
        <div class="column is-narrow">
            <input type="submit" value="작성완료"
                   class="button is-primary">
        </div>
    </div>
</form>
{% endblock form %}


{% block vue_script %}
<script>
    app._data.date = new Date('{{ form.join_date.data or today_date() }}')
</script>
{% endblock vue_script %}

```



#### 05 route: auth.employee_invite_accept  => admin.employee_add route 처리과정과 똑같은 로직을 작성하되, invite의 is_answered, is_accepted의 추가처리가 있다.

```python
@auth_bp.route('/invite/employee/accept/<int:id>/', methods=['GET', 'POST'])
@login_required
def employee_invite_accept(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)
        # 1) 수락했으면, [해당 invite]에서 invitee와, role을 가져와 수정한다
        #  => 모든 정보가 입력되면 is_answered된 상태 & is_accepted 처리까지 해줘야한다.
        # invite.is_answered = True
        # invite.is_accepted = True
        # db.session.add(invite)

        # 2) 수락했으면, invitee인 [User]의 기본정보를 위해  user객체를 구해온다
        invitee_user = db.session.get(User, invite.invitee_id)
        # 3) 수락했으면, invter 정보 대신 role_id로 해당 [Role]을 배정해줘야한다
        role = db.session.get(Role, invite.role_id)

        form = EmployeeForm(invitee_user, role=role)

    if form.validate_on_submit():
        #### user ####
        user_info = {
            'email': form.email.data,
            'sex': form.sex.data,
            'phone': form.phone.data,
            'address': form.address.data,
            'role_id': form.role_id.data,
        }
        invitee_user.update(user_info)
        f = form.avatar.data
        if f != invitee_user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)
            delete_uploaded_file(directory_and_filename=invitee_user.avatar)
            invitee_user.avatar = f'avatar/{filename}'

        #### employee ####
        # - role은 employee에  있진 않다. 부모격인 user객체에 들어가있음.
        employee = Employee(
            user=invitee_user,
            name=form.name.data,
            sub_name=form.sub_name.data,
            birth=form.birth.data,
            join_date=form.join_date.data,
            job_status=form.job_status.data,
        )

        #### invite ####
        invite.is_answered = True
        invite.is_accepted = True

        with DBConnectionHandler() as db:
            db.session.add(invitee_user)
            db.session.add(employee)
            #### invite 처리####
            db.session.add(invite)
            db.session.commit()
            flash("직원 전환 성공")

        return redirect(url_for('auth.userinfo'))

    return render_template('auth/userinfo_employee_form.html',
                           form=form)

```



##### 버그 수정) select를 1개로 고정할 땐, chocies + diabled 외에 .data도 처리해줘야한다. 보이기만 1개로 보이고, 이미 존재하던 값으로 내부에서 덮어씌여져서 choice validator에 걸리기 때문이다.

```python
# 2) role=은 [직원초대]를 보낼 때 EmployeeInvite에 담긴 role_id => 해당role 1개만 지정되며 수정불가능하게 비활성화한다.
if role:
    #### select는 필드의 값을 미리 채울 때, .data가 아니라 .choices에 tuple1개 list를 1개만 넘기면 된다.
    # cf) view에서는 subfield.data, subfield.label로 쓰임
    self.role_id.choices = [(role.id, role.name)]
    # role의 choie를 1개만 배정해놓고, 더이상 수정 불가능하게 막아주자.
    self.role_id.render_kw = dict(disabled=True)
    # choice만 주면, 기존user정보로 필드의.data가 채워진 상태로, 보이기만  choices1개만 보여지게 된다.
    self.role_id.data = role.id

```



![image-20221221201614764](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221201614764.png)



#### 06 응답처리후 응답안된 것들만 필터링(받은초대 조회 + 초대보낼때 존재검사) 및 중복 직원초대처리하기

![image-20221221202432411](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221202432411.png)

#### 07 초대수락하여 내가 이미 staff가 되는 상황이라면,  여러사람이 보낸, 같은 목적의 Staff초대는 일괄 삭제? => 일괄거절( + 일괄응답) 로 처리하자.

- accept로직에 

  - **현재 invite를 제외한 / 유효한 invite  중에 / 나에게 온 invite들을 `is_accepted  False` + `is_answerd  False`로 주기**

    ```python
    with DBConnectionHandler() as db:
        db.session.add(invitee_user)
        db.session.add(employee)
        #### invite 처리####
        db.session.add(invite)
    
        #### 수락한 초대를 제외한, 나에게 보낸 [다른 직원초대들 일괄 거절] 처리
        stmt = (
            update(EmployeeInvite)
            .where(EmployeeInvite.id != id)  # 현재 초대를 제외한
            .where(EmployeeInvite.is_not_expired)  # 아직 유효한 것들 중
            .where(EmployeeInvite.invitee == invitee_user)  # 나에게 보낸 직원초대들
            .values({EmployeeInvite.is_accepted: False, EmployeeInvite.is_answered: True})
        )
        # print(stmt)
        # UPDATE employee_invites SET is_answered=:is_answered, is_accepted=:is_accepted WHERE employee_invites.id != :id_1 AND employee_invites.create_on >= :create_on_1 AND :param_1 = employee_invites.invitee_id
    
        db.session.execute(stmt)
        db.session.commit()
        flash("직원 전환 성공")
    ```

    

    ![image-20221221212539726](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221212539726.png)



#### 08 응답처리된 is_answered == True는  보낼때exist검사 / 받을때 조회에 제외시켜 안보이게 하기

##### InviteBaseModel에서 is_not_expired에 추가로 is_not_answered를 hybrid_property로 만든다

- **expression은 `not  ~ `이 안되고 ` ~ == False`로 직접 비교하여 ClauseElement obj를 만들어야한다. 직접 True/False가 떨어지면 안된**

```python
    @hybrid_property
    def is_not_answered(self) -> bool:
        return not self.is_answered

    @is_not_answered.expression
    def is_not_answered(cls):
        # return not cls.is_answered
        return cls.is_answered == False
```



##### is_not_answered + is_not_expired를 합쳐서, is_valid를 만들자

- 한번에 만들면 어려웟겠지만 **expression을 이용한 expression을 만들었다.**

```python
@hybrid_property
def is_valid(self) -> bool:
    return self.is_not_expired and self.is_not_answered

@is_valid.expression
def is_valid(cls):
    return and_(cls.is_not_expired, cls.is_not_answered)


```



##### 이제 user로 invitee를 조회할 때, is_not_expired => is_valid ( expired + answer 안된 것)으로 조회한다.

```python
    @classmethod
    def get_by_invitee(cls, user):
        with DBConnectionHandler() as db:
            stmt = (
                select(cls)
                .where(cls.invitee == user)
                # .where(cls.is_not_expired)
                .where(cls.is_valid)
            )
            # print(stmt)
            # SELECT employee_invites.is_answered, employee_invites.is_accepted, employee_invites.create_on, employee_invites.key, employee_invites.id, employee_invites.inviter_id, employee_invites.invitee_id, employee_invites.role_id
            # FROM employee_invites
            # WHERE :param_1 = employee_invites.invitee_id
            # AND employee_invites.create_on >= :create_on_1
            # AND employee_invites.is_answered = false

            invite_list = db.session.scalars(stmt).all()
        return invite_list
```



![image-20221221214112645](../../../Users/is2js/AppData/Roaming/Typora/typora-user-images/image-20221221214112645.png)

#### 09 is_not_expired가 사용된 곳 모두를 is_valid로 필터링 조건 바꿔주기

![image-20221221214416425](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221214416425.png)

- admin.employee_invite route: 직원초대 누를 때, 중복되는지  exists검사
- auth.employee_invite_accept: 직원 수락한다면, 나를 제외한 나머지 조회해서 거절+응답처리



##### test

![image-20221221214929760](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221214929760.png)

- 둘중에 하나만 수락한다

![image-20221221215017810](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221215017810.png)

![image-20221221215025712](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221215025712.png)

![image-20221221215043793](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221221215043793.png)







### 직원 edit 구현(add는 직접추가X 전환 or 초대로만)

#### employee_edit

```python
@admin_bp.route('/employee/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee_edit(id):
    # 1) user기본정보는, employee 1:1 subquery로서 바로 찾을 수 있기 때문에 조회는 생략한다.
    # employee화면에서는, employee id를 보내주기 때문에 user_id와 별개로 id로 찾는다.
    with DBConnectionHandler() as db:
        employee = db.session.get(Employee, id)
    # 2) employeeForm이 수정form일땐, role선택여부를 위해 g.user가 고용주로 들어가며
    #   기본정보인 user정보를 채우기 위해, user도 들어간다.
    form = EmployeeForm(employee.user, employee=g.user)

    return render_template('admin/employee_form.html',
                           form=form
                           )
```



##### 링크 연결

```python
<a href="{{url_for('admin.employee_edit', id=employee.id)}}" class="tag is-success is-light">
    <span class="icon">
    <i class="mdi mdi-square-edit-outline"></i>
    </span>
    수정
</a>
```

![image-20221222002605080](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222002605080.png)





#### EmployeeForm 버그 fix.  부모생성자에 kwargs를 넣어줄 땐, 언패킹하지말고 dict를 인자로

```python
	    def __init__(self, user,
                 employer=None, role=None, # 직원전환시 상사객체 OR 직원초대시, role객체 =>  role을 선택할 수 있거나 role을 미리 채운다
                 employee=None, # 수정을 위한 미리생성된 user의 employee객체
                 *args, **kwargs):

        self.employee = employee
        self.employer = employer
        self.role = role
        if self.employee:
            #### 부모가 (user, *args, **kwargs)를 받는 상항이라면
            #### => 자식이 부모에 keyword를 넣어준다면, dict를 언패킹안하고 그냥 넣어주면 된다.
            ####    사실상 파라미터가 아니라 인자호출이라서, dict는 그대로 넣어주면 된다.
            # super().__init__(**self.employee.__dict__)
            super().__init__(user, self.employee.__dict__)
```

