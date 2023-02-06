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





### EmployeeForm 버그 fix.  부모생성자에 kwargs를 넣어줄 때, 부모는 user를 언패킹해쓰고, employee는 keyword로 들어갈 것인데, 공통된 key들이 겹침.

```python
        if self.employee:
            super().__init__(user, **self.employee.__dict__)
```

![image-20221222144214864](../../../Users/is2js/AppData/Roaming/Typora/typora-user-images/image-20221222144214864.png)

- `user`객체와, employee속 관계필드`user`이 부모form에서 같은keyword로 들어가게 되 중복된다.
  - user -> UserinfoForm에서 수정form으로서 unpacking
  - employee -> EmployeeForm에서 수정Form으로서 unpacking
    - UserinfoForm에서 keywrod로 관계객체 user가 또 들어감
    - **그외 add_date, pub_date의 base공통칼럼**과 **관계칼럼 등을 제거하고 dict로 만드는 메서드가 필요함**

#### BaseModel에 to_dict 기본 정의해주고, 각 모델마다 필요없는 key del해서 반환하도록 해주기

- serialize 참고 : https://stackoverflow.com/questions/7102754/jsonify-a-sqlalchemy-result-set-in-flask
- **sqlalchemy의 `inspect( model객체 )`.attrs.keys()를 활용하면 `model객체의 필드값`만 받을수 있다**
  - .dict시 나타나는 sa_ 등의 제거 가능

```python
class BaseModel(Base):
    __abstract__ = True

    add_date = Column(DateTime, nullable=False, default=datetime.datetime.now)
    pub_date = Column(DateTime, nullable=False, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def to_dict(self):
        return {c: getattr(self, c) for c in inspect(self).attrs.keys()}

    @staticmethod
    def to_dict_list(l):
        return [m.to_dict() for m in l]
```

- **상속 Entity에서는, `부모의 기본to_dict()`호출후, `필요없는 key를 삭제하고 반환`해준다.**

```python
class Employee(BaseModel, Serializer):
    __tablename__ = 'employees'
    
   #...
    
   def to_dict(self):
        d = super().to_dict()
        del d['add_date'] # base공통칼럼을 제외해야 keyword가 안겹친다
        del d['pub_date']
        del d['user'] # 관계객체는 굳이 필요없다.
        del d['id']
        return d
```

#### form에서 언패킹할 때, to_dict()로 정제된 dict를 넘겨, 부모의 user객체 언패킹에서 안겹치게 한다

```python
class EmployeeForm(UserInfoForm):
    #...
    def __init__(self, user
        #...
                 
		if self.employee:
            super().__init__(user, **self.employee.to_dict())

```



![image-20221222153238359](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222153238359.png)



#### fix2 role은 employer 상급자보다 수정하는 직원의 직위가 높은 경우, choices에 안나타나서, 본래role이 초기화되어 사라져버린다 => admin만 가능하게 하거나, 자신보다 직급낮을때만 수정 가능하게 해야한다.

![image-20221222005811344](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222005811344.png)

![image-20221222005818033](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222005818033.png)

##### 자신보다 직급 낮은 사람만 [직원관련 UD가 가능하도록 조건문] 걸기 by Role.is_less_than()

```html
<!-- 수정은 g.user의 role미만이 choices로 구성되므로, 자신보다 낮을때만 수정되게 해야한다. -->
{% if employee.user.role.is_under(g.user.role) %}
<a href="{{url_for('admin.employee_edit', id=employee.id)}}" class="tag is-success is-light">
    <span class="icon">
        <i class="mdi mdi-square-edit-outline"></i>
    </span>
    수정
</a>

<a href="{{url_for('admin.employee', id=employee.id)}}" class="tag is-warning is-light">
    <span class="icon">
        <i class="mdi mdi-trash-can-outline"></i>
    </span>
    퇴사
</a>


<a href="{{url_for('admin.employee', id=employee.id)}}" class="tag is-danger is-light">
    <span class="icon">
        <i class="mdi mdi-trash-can-outline"></i>
    </span>
    삭제
</a>
{% endif %}
```



![image-20221222010209689](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222010209689.png)



##### view에서 걸지말고, 백엔드에서 권한확인후 낮으면 redirect

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

    #### 직원관련 수정 등은, role구성이 자신이하로만 구성되므로, 조건을 확인하여, 아니면 돌려보내보자
    if not employee.user.role.is_under(g.user.role):
        flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
        return redirect(redirect_url())

    form = EmployeeForm(employee.user, employee=employee, employer=g.user)

    return render_template('admin/employee_form.html',
                           form=form
                           )

```



![image-20221222011103383](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222011103383.png)





#### fix3. employer의 role로choice를 구성할 때, 미리 .data, .name을 주입하면, form에서 select한 데이터가 아니라 주입한 데이터가 올라온다 => 선택사항이 있을 땐, .data 초기화는 삭제

![image-20221222155305829](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222155305829.png)

![image-20221222155350702](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222155350702.png)



#### employee_edit route

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

    #### 직원관련 수정 등은, role구성이 자신이하로만 구성되므로, 조건을 확인하여, 아니면 돌려보내보자
    if not employee.user.role.is_under(g.user.role):
        flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
        return redirect(redirect_url())

    # 항상 수정form을 만드는 user / employform의 수정form인 employee= / role이 1개가 아니라, g.user이하의 role을 만드는 employer=
    form = EmployeeForm(employee.user, employee=employee, employer=g.user)

    if form.validate_on_submit():
        #### user ####
        user_info = {
            'email': form.email.data,
            'sex': form.sex.data,
            'phone': form.phone.data,
            'address': form.address.data,

            'role_id': form.role_id.data,
        }
        user = employee.user
        user.update(user_info)

        f = form.avatar.data
        if f != user.avatar:
            avatar_path, filename = upload_file_path(directory_name='avatar', file=f)
            f.save(avatar_path)
            delete_uploaded_file(directory_and_filename=user.avatar)
            user.avatar = f'avatar/{filename}'

        #### employee ####
        employee_info = {
            'name': form.name.data,
            'sub_name': form.sub_name.data,
            'birth': form.birth.data,
            'join_date': form.join_date.data,
            'job_status': form.job_status.data,
            #### 수정된 user객체를 넣어준다
            'user': user,
            #### 생성시에 없었던, job_status와, resign_date를 넣어준다
            # 'job_status': form.job_status.data,
            # 'resign_date': form.resign_date.data,
        }
        employee.update(employee_info)

        with DBConnectionHandler() as db:
            db.session.add(employee)
            db.session.commit()
            print(employee.user.role_id)
            flash("직원 수정 성공", category='is-success')

        return redirect(url_for('admin.employee'))

    return render_template('admin/employee_form.html',
                           form=form
                           )

```





### 퇴사처리 => 재직상태 변경

#### 퇴사처리(job_status변경+resing_date 할당)는 form에서 수정안되고, 버튼으로만 처리하되, executive이상만 허용하게 한다.

#### 01 퇴사버튼 대신 재직상태변경으로 바꾸고, [직원초대]처럼 modal을 띄워서, jobstatus를 고르게 할 수 있어야한다

![image-20221222160913699](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222160913699.png)

#### 02 modal 정리

##### 01 route로 가던 a href에 1) modalactive변수 true,  modal전달변수 = id할당을 한다

```html
<a href="javascript:;"
   @click="isJobStatusModalActive = true; employee_id = {{employee.id}}"
   class="tag is-warning is-light"
   >
    <span class="icon">
        <i class="mdi mdi-trash-can-outline"></i>
    </span>
    재직상태변경
</a>
```

##### 02 base.html의 data에서 2개 변수를 초기화한다

```js
//employee.html modal 띄우는 변수
isJobStatusModalActive: false,
employee_id: null,
```



##### 03 다시 원래html의 끝부분에 b-modal을 v-model isModalActive로 선언하여 인식하게 한다. 다시 누를 땐, 변수 2개를 false, 및 다시 null로 초기화한다

- `has-modal-card` 속성을 붙여줘야, 카드모양으로 이쁘게 나온다
- 완료버튼외에 닫기버튼들에 대해 `@click = "  isModalActive = false; 전달변수 =null;"`을 넣어줘서 v-model을 인식해서 닫히게 한다

```html
<b-modal
        v-model="isJobStatusModalActive"
        has-modal-card
        trap-focus
        aria-role="dialog"
        aria-label="Role Select Modal"
        aria-modal
        >

    
</b-modal>
```

```html
<!-- 재직상태변경 모달 -->
<b-modal
        v-model="isJobStatusModalActive"
        has-modal-card
        trap-focus
        aria-role="dialog"
        aria-label="Job Status Select Modal"
        aria-modal
>
    <div class="modal-card is-" style="width: auto">
        <header class="modal-card-head">
            <p class="modal-card-title is-size-5">
                재직상태 변경
            </p>
            <button
                    type="button"
                    class="delete"
                    @click="isJobStatusModalActive = false; employee_id = null;"/>
        </header>
        <section class="modal-card-body">


        </section>
        <footer class="modal-card-foot">
            <!-- b-button들을 넣으면 1개 이후 사라지는 버그 => a태그 + input(submit) 조합으로 변경-->
            <a class="button is-primary is-light mr-2"
               @click="isJobStatusModalActive = false; employee_id = null;"
            >
                닫기
            </a>
            <input type="submit"
                   class="button is-primary"
                   value="완료">
        </footer>
    </div>

</b-modal>
```



![image-20221222191445258](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222191445258.png)





##### 04 안쪽에 form에 action에  card들을 씌운다. b-button 1개만표시 버그 때문에, a.button 과 input[type='submit'].button 조합으로 이루어진다. 전달받은 id변수는 `:value`로  hidden인풋에 넣어준다

- action에 걸 route는 추후 만들어지므로 일단 비워둠
- **IntEnum의 .chocies로 가져와 튜플list로 보내주므로 `view에서는 [0], [1]`로 인덱싱해서 써야한다**



```html
 <form action="" method="post">
        <div class="modal-card is-" style="width: auto">
            <header class="modal-card-head">
                <p class="modal-card-title is-size-5">
                    재직상태 변경
                </p>
                <button
                        type="button"
                        class="delete"
                        @click="isJobStatusModalActive = false; employee_id = null;"/>
            </header>
            <section class="modal-card-body">
                <!-- INPUT1: HIDEEN 모달클릭시 v-bind변수에 담아놨던 변수로, form에 포함될 변수로서 id를 반영 -->
                <input type="hidden" name="employee_id" :value="employee_id">

                <!-- INPUT2:  -->
                <b-field label="재직상태">
                    <!-- option이 아니라 상위 b-select에  name=도 같이붙으며  form으로 간다 -->
                    <b-select
                            name="job_status"
                            placeholder="재직상태 선택"
                            rounded required
                    >
                        {% for job_status in job_status_list %}
                        <option value="{{job_status[0]}}" selected>{{job_status[1]}}</option>
                        {% endfor %}
                    </b-select>
                </b-field>

            </section>
```



![image-20221222192533719](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222192533719.png)

##### 05 폼에 select option을 구성할 요소를 추가로 route에서 내려보내줘야한다

```python
@admin_bp.route('/employee')
@login_required
@role_required(allowed_roles=[Roles.CHIEFSTAFF])
def employee():
    page = request.args.get('page', 1, type=int)

    stmt = select(Employee) \
        .where(Employee.is_active) \
        .order_by(Employee.join_date.desc())

    pagination = paginate(stmt, page=page, per_page=10)
    employee_list = pagination.items

    #### 재직상태변경을 modal 속 select option 추가로 내려보내기
    job_status_list = JobStatusType.choices()
    # print(job_status_list)
    # [(1, '재직'), (2, '휴직'), (3, '퇴사')]

    return render_template('admin/employee.html',
                           employee_list=employee_list,
                           pagination=pagination,
                           job_status_list=job_status_list
                           )

```



![image-20221222194041952](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222194041952.png)



#### 03 modal의 post처리 route

![image-20221222201005869](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222201005869.png)



- 퇴사처리 확인

  ![image-20221222201038262](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222201038262.png)

  ![image-20221222201059807](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222201059807.png)

- **employee 조회시, is_active에는 `대기=0, 퇴사=4`를 제외하고 가져오기 때문에, 안나타난다**

  - 일단 다 가져오도록 변경해놓기(대기가 없기 때문)

  ```python
  @admin_bp.route('/employee/job_status', methods=['POST'])
  @login_required
  @role_required(allowed_roles=[Roles.CHIEFSTAFF])
  def employee_job_status_change():
      employee_id = request.form.get('employee_id', type=int)
      job_status = request.form.get('job_status', type=int)
  
      with DBConnectionHandler() as db:
          employee = db.session.get(Employee, employee_id)
  
          if not employee.user.role.is_under(g.user.role):
              flash('자신보다 아래 직위의 직원만 수정할 수 있습니다.', category='is-danger')
              return redirect(redirect_url())
  
          employee.job_status = job_status
          if job_status == JobStatusType.퇴사:
              # print("퇴사처리시 resign_date가 찍히게 된다.")
              employee.resign_date = date.today()
  
          db.session.add(employee)
          db.session.commit()
  
      return redirect(redirect_url())	
  ```





#### 

#### 04 modal action route 및 method post 설정

```html
    <form action="{{url_for('admin.employee_job_status_change') }}" method="post">

```



#### 05 퇴사처리시,  user role을 staff -> user로 변경하고, employee정보는 그대로 두기

```python
employee.job_status = job_status
if job_status == JobStatusType.퇴사:
    # print("퇴사처리시 resign_date가 찍히게 된다.")
    employee.resign_date = date.today()
    # 퇴사처리시 role을 user로 다시 바꿔, 직원정보는 남아있되, role이 user라서 접근은 못하게 한다
    employee.user.role = Role.get_by_name('USER')

```

![image-20221222203709480](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222203709480.png)

![image-20221222203720819](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222203720819.png)





#### 06 퇴사자가 다시 직원초대를 받으면?, 직원정보다 또 생길 듯?

![image-20221222203932549](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222203932549.png)



##### user-employee는  uselist=False의 1:1관계인데, 추가데이터가 들어온 순간 None으로 인식된다. => user를 새로 가입하거나 or 기존 employee정보를 없애야한다

![image-20221222204336511](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222204336511.png)

- 1:1관계의 데이터가 추가되면, **기존 데이터는 fk에 null이 차버린다.**

  ![image-20221222212226479](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212226479.png)

  - 삭제하고 , 재입사로직을 넣은 뒤 다시 해보자.



#### 07 직원초대 accept route에서, 해당user_id로 employee정보가 발견되는 경우를 찾아서 미리 삭제하여 1:1관계 유지하기 + Employee에 [admin용 비고 칼럼] 만들어서, [재입사] 기입해놓기?

1. admin으로 staff한명을 퇴사처리하기

   ![image-20221222212400854](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212400854.png)

2. employee정보에는, `퇴사`로 찍히고, role은 user가 되서 User관리에서도 발견됨.

   ![image-20221222212432530](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212432530.png)

   ![image-20221222212456750](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212456750.png)

   

3. 직원초대를 보내고, 해당 유저로 접속. 직원초대 수락해서 작성하기

   ![image-20221222212535517](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212535517.png)

   ![image-20221222212643127](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212643127.png)

4. 이번엔 에러안나고 작성완료

   - 기존employee가 있어서 1:1관계유지를 위해  삭제됬을 것이다.

     ![image-20221222212708239](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222212708239.png)

   - **print**

     ```
     DELETE FROM employees WHERE employees.user_id = :user_id_1
     <sqlalchemy.engine.cursor.LegacyCursorResult object at 0x00000193B455CD68> <class 'sqlalchemy.engine.cursor.LegacyCursorResult'>
     재입사를 위해 기존 입사정보를 삭제했습니다.
     
     ```

5. 기존 직원정보가 없는 새 User의 직원초대도, employee삭제로직을 한다면

   - **입사정보없는데도 execute결과인 LegacyCursorResult는 True로 반영된다.**

   ```
   DELETE FROM employees WHERE employees.user_id = :user_id_1
   <sqlalchemy.engine.cursor.LegacyCursorResult object at 0x00000193B5924BE0> <class 'sqlalchemy.engine.cursor.LegacyCursorResult'>
   재입사를 위해 기존 입사정보를 삭제했습니다.
   
   ```

6. **일반적인 execute결과로는 바로 판단 못한다.**

![image-20221222214323031](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222214323031.png)

![image-20221222214336519](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221222214336519.png)



#### 08 초대수락form 처리route에 해당Invite의 invitee_id의 User가 Employee에 user_id로 이미 존재한 퇴사자면, 1:1관계 유지를 위해 데이터 삭제

- 한번 조회된 객체를 다른 session에서 사요하다가 꼬여서 전부 각 session에서만 사용하도록 변경



##### invite에 포함된 있는 user_id 값을 찾기 위한 .scalar_subquery()

- `id` (Invite) 로 해당 EmployeeInvite를 찾고
  - 그 EmployeeInvite에 있는 `.invitee_id`를 `user_id`로서 찾은 뒤
    - Employee에서 해당 `user_id`로 `employee객체`가 .first()로 가져와
      - 존재하면, 재입사로서 삭제
        - 이 때, Employee의 `비고`란에 `재입사`라고 작성해도 될 것 같다.
      - 존재하지 않으면, 삭제안함.
- **query를 바로 날려서 값을 얻어오지 않고, `1개의 값을 where에서 사용이라면, 찾아서 .scalar_subquery()`에 넣고 주`stmt의 where에 사용`한다**

```python
is_re_join = False
#### Employ정보를 생성하기 전에, 퇴사후 재입사인 경우 user:emp 1:1관계를 유지하기 위해
#### => 기존  employee정보를 검색해서 있으면 삭제해준다
with DBConnectionHandler() as db:
    # 1) invite id -> invite -> invitee_id 값 찾기
    user_id_scalar = (
        select(EmployeeInvite.invitee_id)
        .where(EmployeeInvite.id == id)
    ).scalar_subquery()
    # 2) invite_id값과 user_id가 일치하는 Employee데이터 조회하기
    stmt = (
        select(Employee)
        .where(Employee.user_id ==
               user_id_scalar
              )
```

```python
# SELECT employees.add_date, employees.pub_date, employees.id, employees.user_id, employees.name, employees.sub_name, employees.birth, employees.join_date, employees.job_status, employees.resign_date
# FROM employees
# WHERE employees.user_id = (SELECT employee_invites.invitee_id AS user_id
#                               FROM employee_invites
#                               WHERE employee_invites.id = :id_1)
prev_employee = db.session.scalars(
    stmt
).first()

if prev_employee:
    print("기존 입사정보가 있어서, 삭제하고 재입사 처리합니다.")
    is_re_join = True
    db.session.delete(prev_employee)
    db.session.commit()
else:
	print("기존 입사정보 없이, 신규입사입니다.")

```



#### 09 이제 새로운 Employee정보 생성 commit전에, is_re_join=True면, 비고란(reference칼럼)에 "재입사"를 아니면 "신규입사"를 동적으로 입력시킨다

- 재입사여부확인로직 <-> Employee 생성로직이 다른 sesion이므로 **flag변수를 활용한다**

```python
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

# Employee검사에서 재입사면, nullable인 reference 비고필드를 채워준다.
if is_re_join:
    employee.reference = '재입사'
else:
    employee.reference = '신규입사'
```

#### 10 비고를 직원관리에 넣고, 신규입사 재입사 확인해보기

![image-20221223135612711](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221223135612711.png)







### 수락거절 처리하기

#### 01 employee_invite_reject route

- 초대수락은 form을 처리해야하므로 get+post였지만,
- 초대거절은 only post -> redirect로 처리해야한다

```python
@auth_bp.route('/invite/employee/reject/<int:id>/', methods=['POST'])
@login_required
def employee_invite_reject(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)

        invite.is_answered = True
        invite.is_accepted = False

        db.session.add(invite)
        db.session.commit()

        flash("초대를 거절했습니다.", category='is-danger')

        return redirect(redirect_url())

```



#### 02 userinfo_invitee.html link 연결

```html
<a class="level-item button is-primary is-light is-small"
   href="{{url_for('auth.employee_invite_reject', id=invite.id)}}"
   >
    <span style="margin-right: 1px;" class="icon"><i class="mdi mdi-close"></i></span>
    거절
</a>
```



![image-20221223143747826](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221223143747826.png)

#### 03 a태그로는 post를 보낼 수 없다. 무조건 form에 감싸고나서, type="submit"만 가능한듯.

- **뒤로가기 a태그  +  input type='submit'**조합으로 각각 class에 button을 줬었는데
  - **input태그안에는 value=""로 텍스트만 넣을 수 있고, `아이콘 등은 넣을 수 없다`**
  - **`a태그`는 type='submit'을 넣을 수 없고 `post를 보낼 수없다`**
    - 뒤로가기만 가능
- **`button type ='submit' + 내부요소 조합을 추가`**한다

```html
<!-- 거절과 연기는 only form - post로 요청하여 redirect받기 -->
<form action="{{url_for('auth.employee_invite_reject', id= invite.id) }}" method="post">
    <button type="submit"
            class="level-item button is-primary is-light is-small"
            >
        <span style="margin-right: 1px;" class="icon"><i class="mdi mdi-close"></i></span>
        거절
    </button>
</form>
```





![image-20221223144834232](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221223144834232.png)





### 초대버튼 중복클릭 금지?

- 참고: https://renatello.com/prevent-multiple-form-submissions-in-vue-js/
- 참고2: https://stackoverflow.com/questions/22363838/submit-form-after-calling-e-preventdefault

![image-20221223145700094](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221223145700094.png)

#### 01 form에 action + method를 유지한체, @submit.prevent="submitForm" 메서드를 걸어준다

```html
<!-- 거절과 연기는 only form - post로 요청하여 redirect받기 -->
<form action="{{url_for('auth.employee_invite_reject', id= invite.id) }}"
      method="post"
      @submit.prevent="submitForm"
      >
    <button type="submit"
            class="level-item button is-primary is-light is-small"
            >
        <span style="margin-right: 1px;" class="icon"><i class="mdi mdi-close"></i></span>
        거절
    </button>
</form>
```



#### 02 비활성화될 button등 type="submit"요소에는 :disabled="isLoading" 을 걸어준다

```html
<button type="submit"
        class="level-item button is-primary is-light is-small"
        :disabled="isLoading"
        >
```



#### 03 base.html에서 data- isLoading변수 + methods- submitForm을 정의해준다

- 클릭되면 
  1. **isLoading을 true로 걸어줘서, 버튼이 disabled되게 한다**
  2. **기존 submit event를 다시 submit시킨다**
  3. 1초후에 버튼이 활성화되도록 isLoading을 false로 다시 걸어준다

```js
//employee.html modal 속 제출 처리 변수
isLoading: null,
```

```js
//employee.html modal 속 form 제출 처리
submitForm(e) {
    console.log(e)
    // e.preventDefault();
    // 1) 클릭되면 isLoading에 True가 들어가 button이 disable된다
    this.isLoading = true

    // 2) 다시 도로 제출
    e.target.submit();

    // 2) 1초후에 false가 되 button 돌아온다
    setTimeout(() => {
        this.isLoading = false
    }, 1000)
},
```



- 클릭이 2번부터는 안들어가게 된다. 칼 적용은 안되나보다.









### 초대 연기

#### route

```python
@auth_bp.route('/invite/employee/postpone/<int:id>/', methods=['POST'])
@login_required
def employee_invite_postpone(id):
    with DBConnectionHandler() as db:
        invite = db.session.get(EmployeeInvite, id)

        invite.create_on = invite.create_on + datetime.timedelta(days=EmployeeInvite._INVITE_EXPIRE_DAYS)

        db.session.add(invite)
        db.session.commit()

        flash(f"초대를 {EmployeeInvite._INVITE_EXPIRE_DAYS}일 연기했습니다.", category='is-info')

        return redirect(redirect_url())

```

#### a태그대신 button으로 변경하기

```html
<form action="{{url_for('auth.employee_invite_postpone', id= invite.id) }}"
      method="post"
      @submit.prevent="submitForm"
      >
    <button type="submit"
            class="level-item button is-light is-small has-text-dark"
            :disabled="isLoading"
            >
        <span style="margin-right: 1px;" class="icon"><i class="mdi mdi-timer"></i></span>
        연기({{ invite.remain_timedelta | format_timedelta }})
    </button>
</form>
```



![image-20221223163255918](https://raw.githubusercontent.com/is3js/screenshots/main/image-20221223163255918.png)