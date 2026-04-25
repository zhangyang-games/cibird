#!/usr/bin/env python3
"""
CiBird 词鸟 - 多邻国单词批量导入脚本
用法：python3 import.py 多邻国单词本.txt
"""

import sys
import sqlite3
import json
from pathlib import Path

DB_FILE = Path(__file__).parent / "cibird.db"

RAW = """night
夜，晚上，暗夜

a quarter past
过一刻

a quarter to
差一刻

twin
双胞胎

at the same time
在同一时间，一边，同时

fight
干上，打斗，打仗

shout
地喊，喊道，大喊

half past
半

finish work
下班

finish school
放学，毕业

February
二月，二月份，2 月

eleventh
十一，第十一

tenth
第十，第十位，第

begin
动手，迈入，开篇

what is the date of
是几月几号

December
十二月，十二月份，12 月

until
为止，截至，离下

sixth
第六，第六个，第六名

fourth
第四

start school
开始上课，开学

September
九月，九月份，9 月

October
十月，十月份，10 月

date
舞伴，day，日期

busiest
最忙，最忙的

busier
更忙，越忙

put
摆放，给，放进

refrigerator
冰箱，冷藏箱

swimming pool
游泳池

happiest
最开心，最开心的

happier
更开心

funniest
最有趣的，好笑，最有趣

grandparents
外公外婆，爷爷奶奶，姥爷姥姥

funnier
更好笑，更有趣

sunnier
更晴朗的

hole
坑洞，洞，大洞

home
家

each
每座，一个个，每位

the key to
的钥匙

plant
埋，种出，种花

fattest
最胖，最胖的

dining
餐饮，吃喝

fat
肥，很胖的，胖

hotter
热多，热，更热

hottest
最热的，最热，最火

fatter
更胖

dining room
餐厅

biggest
最大的，最大

its
其，它的，它

bigger
大，更大，更大的

living room
客厅

bookcase
书柜

television
电视，视，电视机

willing
有意，肯，自愿

marry
娶，婚，嫁给

he'll
他会，他将会，他就会

the day after tomorrow
后天

there
那边，那儿，有

library
图书馆

we'll
我们会，我们将要，我们打算

them
它们，他们，她们

you'll
你会，你们，你

ask
提问，问，wondering

be
当，很，be

as well
也，也是

theater
戏剧，剧院，电影院

give
献上，给，给出

go out
灭了，坏了，出门

us
咱们，我们，我們

come with
带

pace
速度，进度，步调

dance party
舞会

invite
邀请，要约，邀约

where will
会住在哪里，会在哪里，会去哪里

they'll
他们会，他们将会，它们会

traffic
车流，堵车，堵

choose
我选，选用，挑

travel to
去旅行

she'll
她会，她将会，她就会

won't
不会，将不会，不

who will
谁会

i'll
我会去，我就会，我会

when will
什么时候

before
前能，早些时候，之前

come home
回家

will not
不会

move to
搬到

month
一个月，份，月份

worried
担，着急，慌张

get married
结婚，结婚的

married
已结婚，已婚，婚

will
里会，刀会，會

get a job
找一份工作

between
彼此之间，之，其间

past
过

inside
里面，in，儿里

turn
拐弯，轮到，变成

there's
有，是

end
收官，结了，末

end of
街尾，尽头

close to
靠近，快到，附近

street
街上，街，一条街

dangerous
危险的

worst
最坏，到头，最差的

look for
寻找，找

safe
安全的，很安全，安

better
好些，好多了，好

worse
更差的，差，更糟糕

coffee shop
咖啡馆

town
镇上，都市，城镇

zoo
动物园

smoking
冒烟，烟熏，抽

cannot stop
不能停，不能停止

grandmother
祖母，奶，姥

grandfather
祖父，外爷

hope
希，希望，望

smoke
冒烟，烟，烟雾

bad for
难过

good for
适合

angry
气，生气的，生......的气了

feel
体会，摸起来，感到

radio
收音机，广播，无线广播

tired
累，疲惫的

listen to
听

enjoy
欢，享，爱

listen
闻闻，听听，聆听

fit
身材很好，胜任，装不下

kid
小山羊，孩，子

companies
公司，们，日本公司

because
因为

writing
文笔，写字，写长

speaking
说话，口语，正说

hard
不易，用力，硬质

schedule
时间表

early
早早，很早，幼

finish
吃完，结了，吃掉

next year
明年

change
推移，我换，波动

building
楼里，公寓楼，修建

work from home
在家工作

having
进行，办，吃

work for
为...工作

send
捎，会派，电子邮件发送

message
信息，消息，留言

second
秒，二号，第二个

later
后来，迟一些，日后

company
公司，企业

have a nice trip
旅途愉快

coldest
最冷的，最冷

the most interesting
最有趣的

the most expensive
最贵的

trip
摔到，跌倒，行程

take
买下来，包拿得，李了

world
大地，界，世

fastest
最快，快过

in the world
世界上

group
会派，伍，圈子

ticket to
去看

excite
刺激，激发

the most exciting
最令人兴奋的

on tv
电视上，在电视上

the most boring
最无聊的

exciting
令人兴奋的，兴奋的

part
一部分，告别，部

most
最有，大多数，最

the most important
最重要的

host
开了个，东道主，招待

the most famous
最有名的

team
队，伍，团

player
玩家，队员，运动员

June
六月，六月份，6月

May
五月，五月份，可以

say
讲个，读，說

what are
做什么

after
听完后，做后，behind

soon
很快，不久，早

call
地喊，喊道，取名

aren't
不是，不

the time of
的时间

not going to
不打算

practice
练习，践，练

leave
搬离，离开，发车

a.m.
上午，早上，凌晨

p.m.
晚上，下午，晚

meet
见见面，迎来，运动会

row
排，划，垄

going to
打算，要上，要去

tomorrow
明天，明日

uncle
叔，姑夫，姨父

aunt
姑妈，小姨，kim

paper
用纸，文件，篇文章

paint
描绘，上漆，涂

pencil
铅笔

picture
图片，画，图画

dictionary
词典

smallest
最小

smaller
更小的，小，小一点的

subject
科，主题，学科

desk
课桌，桌子，办公桌

oldest
最大的，最旧的，最年

youngest
最小的，最小

more interesting
更有趣

courses
课程，四门

more difficult
更难

course
主菜，课，课程

take a test
参加考试

test
调试，考，考试

down
小，下，低

shortest
最矮的，最矮

tallest
最高的，最高

in the classroom
教室里

classroom
教室

fifteen
十五个，十五岁，十五

how much does
多少钱

cheaper
更便宜，便，更便宜了

fifty
五十，50

get
得，捉到，搞

how much do
多少钱

pairs of
双

color of
颜色，颜色的

pink
粉色的，粉色，平克

forty
四十，40

thirty
三十，30

what do
做什么

cheap
劣质，便，廉

more famous
更有名

more beautiful
更美丽

glasses
杯，玻璃杯，眼镜

pair
配对，双，couple

pair of
双，副，条

more expensive
更贵

blouse
女士衬衫，上装

boot
靴子，后备箱

cost
包要，要价，worth

making
制作，制造，作

day
白天，天，一天

taking
会参加，带，坐

having a good time
过得愉快

having a picnic
野餐

at a cafe
在咖啡馆

taking photos
拍照

have a picnic
去野餐

taking a vacation
度假

have a good time
玩得很开心，玩得开心点

cafe
咖啡馆，咖啡厅，caf

at the beach
在海滩，海滩

on the boat
在船上

location
原地，處，位置

monday
星期一，周一，礼拜一

take a vacation
请假，度假

picnic
野餐

dancing
舞蹈，跳舞，跳跳舞

driving
开，开车，行驶

on holidays
假期时

boat
游船，渡船，船只

riding
骑着，骑着马，骑马

holiday
假日

holidays
假日，假期，节日

relax
放松一下，而松，放心

bicycle
自行车，单车

sweet
悦耳，体贴，甜的

year old
岁

chocolate
巧克力，朱古力

singing
唱，地唱，唱着歌

taller
更高的，更高，高

than
比起，包比，于

low
很低的，低，不足

shorter
更短，更矮，更短的

yellow
黄色

hungry
饿

ice cream
冰淇淋

hunger
饥饿，食欲

cream
药膏，鲜奶油，乳霜

younger
年轻，junior，更年轻

baby
宝宝，婴儿，宝贝

babies
宝宝们，宝宝，婴儿

older
大，更年长，更大

have a party
开派对

boring
无聊

what's up
最近怎么样

hey
喂喂，哎，嘿

gets
变得，得到，买

outside
在外，在外面，外面

go outside
出去

raining
下雨，有雨，下着雨

snowing
下雪，下着雪，雪下

stay
留下来，保持，马住

can't find
找不到

sitting
坐，坐在，着

shopping
购买，买东西，购物

find
查找，得知，找一下

ball
球体，跳舞会，球

waiting for
在等

waiting
等着，等待，等

interesting
有意思的，有趣

running
跑步，跑得，跑

swimming
游泳

what are you doing
你在这里做什么，你们在做什么，你在做什么

wait
数着，候，马住

learning
学，学习，学骑

let's
让我们，咱们，我们一起

sports
体育比赛，体育，运动

fast
飞快，高速，很快

sport
竞技，运动，嬉戏

run
跑步，本跑，运行

wearing
戴，戴着，打着

at home
在家，在家里

gray
灰色的，灰色，灰的

looking for
找，寻找，在找

wear
戴，戴眼镜，破损

can't see
看不到

why
为什么，为何

can't hear
听不到

children
小孩子，小孩，子女

sold
卖了，卖出去，卖掉了

old man
老人

who is
谁是，是

see
见到，看见，目睹

hear
听见，闻闻，聆听

child
孩子

what's
什么是，什么，是什么

look at
看，看看，你看

photo
照片

photos
摄，照片，老照片

come to
来

take photos
拍照片

take a photo of
拍张照片

american
美国的，美国人，美式

where does
在哪儿，在哪里

walk
前行，走得，徒步走

walks
走，走路，步行

goes shopping
去购物

shop
小商店，商店，商家

go to bed
去睡觉

go home
回家

get up
起床，起

can't sleep
睡不着

at night
在晚上，在夜里

take a bath
泡澡

sleep
睡一觉，睡觉，睡

what
什，哪個，多少

what day is it
今天星期几

cooking
烹饪，饪，烹

washing
洗头发，洗碗，洗

cleaning
在打扫，打扫，清理

same
相同，同，一样

drinking
喝啤酒，喝牛奶，喝酒

talking about
谈，谈论，谈谈

came
来了，前来，来

talk about
谈论，谈，讨论

doing
做，在做，干

japanese
日本语，日本人，日本的

playing
打网球，正玩得，玩儿

light
轻度，并点，光线

talking
说话，会说话的，聊天

talking to
和我说话，和一个女孩说话，和我爷爷说话

right now
在，正在，马上

him
他，他别

about
有关，大约，前后

talk to
跟...说话，和...说话

thought
原以为，心思，想

watching
在看，看电视，看

newspaper
报纸，报

eating
在吃，吃，吃饭

we're
我们是，我们正在，我们已经

reading
读，阅，看书

people
十口，guys，人家

young
年轻

happy birthday
生日快乐

sad
难过，伤心的，悲伤

letter
帖，字符，信件

parties
聚会

fun
好玩的

how are you doing
你怎么样

how is
如何，还好吗，好吗

third
三日，三，第

too much
太多的，太多了

think
想着，想，动脑筋

first
第一位，先往，第一名

wednesday
星期三，礼拜三，周三

birthday
生日

march
三月份，行进，行走

March
三月，三月份，3月

July
七月，七月份，7月

party
聚会，派对

pay for
付

how much money
多少钱

money
钱

me
我，自我，我别

help
人手，助，帮个

sit
坐，坐下

wait for
等，等一下

sure
当然，很确定，百分之百

twenty
20，二十分，二十只

plate
盘子，盘，碗盘

mind
理会，内心，心思

what kind of
哪一类的，哪种，什么样的

no, thanks
不，谢谢

yes, please
是的，请

help you
帮助，帮，帮助你

how are you
你好吗，你们好吗，你过得好吗

good afternoon
下午好

can't
不能，没法，就不能

well
做得很好，很好，好好

learn to
学

very well
得非常好，得非常清楚，非常

learn
会得，学得，课学得

piano
钢琴

guitar
吉他，六弦琴

cannot
不得，做不了，不成

dance
舞蹈，过舞，舞会

swim
泳，游，游泳

can
行不行，时能，會

ride
骑过，搭过，人载

drive
动力，驾车，野心

bike
骑自行车，脚踏车，自行车

factories
工厂，厂

visit
看望，光顾，串个

places
地方，哪些地方

meats
肉类

place
處，摆放，坛

in front of
在前面，前面

which
哪张，哪個，哪本

behind
behind，身后，在后面

hide
躲藏，埋，躲

lunch
午饭，午，午餐

dinner
吃晚饭，晚饭，晚宴

make
造出，取得，交

kind of
类

food
食品，东西，粮

would like to
想要

beef
牛肉，牛

nine
九，九个，九位

nineteen
十九

eighteen
十八

women
女人，妇女，女人们

when
的时候，时为，何时

how old are
多大

eight
八

men
男人，guys，男人们

hair
头发，发

brown
棕色，棕色的，棕

eye
眼，目，盯

grandpa
爷爷，外公，爷

watches
观赏，手表，看

grandma
奶奶，姥姥，外婆

bed
床位，病床，小床

washes
洗，清洗，洗碗

teaches
教我如何，教会，教书

face
脸

wash
洗

often
经常

live
生存，不住，我住

hand
手上，手，手们

open
打开，公海，揭开

clothes
衣服，衣物，服装

hundred
百

now
现在

clothes store
服装店

store
储存，店铺，存入

seventeen
十七

different
不同的

t-shirt
T恤衫，短袖

how much are
多少钱

how
如何，多，的方式

both
双，两样，两家

yuan
元，块，块钱

seven
七

how much is
多少钱

wants to
想

sixteen
十六

those
那些，那条，那片

jeans
牛仔裤

skirt
短裙，裙子，裙

dresses
洋装，礼服，连衣裙

six
六

want to
想要，想

buy
买冰，买下来，买昂

go shopping
去购物

guy
男人，guys，人

Saturday
周六，礼拜六，星期六

what is
是什么

closed
关门，封闭，售

last
上一个，最后一座，撑

last name
姓氏，姓

late
迟到，behind，晚点了

first name
名字

go
进行，坐，出发

port
港口，港

ticket office
售票处

hotel
旅馆，酒店，宾馆

need to
需要

bus
公交车，公共汽车，公车

passport
护照，通行证

right
权利，没错，正确的

right here
就在这里

ticket
门票，火车票，票

plane
飞机，层面

over
头顶，整个都，为了

where is
在哪里

over there
在那里

to
为了，而言，來

taxi
出租车，计程车，的士

bathroom
浴室，卫生间，洗手间

subway
地铁，地下铁

the
这只，这瓶，这个

station
铁，进驻，岗位

airport
机场，飞机场

train
火车，列车，培养

speaks
说，讲话，说得

usually
平时，经常

fine
大好，很好，没

time
時間，times，時候

sometimes
有的时候，有时候

uses
用，他用，使用

at school
在学校，学校里

doesn't
不，没，不像

cooks
烹饪，煮，烹调

cook
厨师，烹饪，饪

music
音乐

sing
唱过，唱，唱个

draw
平局，画画，提取

tv
电视机，电视，视

evening
晚上，傍晚，黄昏

does not
不

movie
故事片，电影，影

noodle
面

every
每座，每道，每天

baseball
棒球

does
吗，有，打

tennis
网球

basketball
篮球

lead
领先，头绪，指引

likes to
喜欢

like to
喜欢

play
吹得，地玩，放过

read
读，读归读，阅

seeds
种子，花种

a glass of
一杯

needs
必须，要，需要

potato
土豆，薯，土

tomato
西红柿，柿子，番茄

soup
汤

sandwiches
三明治，三文治

fruit
果实，成果，果

vegetable
蔬菜，蔬

never
从来不

pets
宠物，宠物们

eats
吃，吃饭，吃得

drinks
饮料，喝牛奶，喝酒

wants
想让，想，想要

egg
鸡蛋，蛋，雞

mice
老鼠，鼠

noodles
面条，面，面点

bread
面包

want
想让，想，想要

some
某个，某项，少量

likes
喜欢，很喜欢

rice
米饭，米，大米

eat
吃，食用

link
串起，网址，係

breakfast
早饭，早餐，早点

every day
每天

apple
苹果，苹

use
用，使用

the internet
互联网

city
城市，市，都市

in
里面，用，丁里

Sunday
周日，星期日，礼拜天

sun
阳光，恒星，太阳

Monday
周一，礼拜一，星期一

Tuesday
周二，星期二，礼拜二

on
用，之上，in

university
大学

teach
教，教书

at work
在工作时，上班时，上班

study
调研，求学，我念

tonight
今天晚上，今晚，今夜

beach
海滩，沙滩，沙地

lot
很多，大堆

rank
伍，秩，品位

a lot of
很多，许多

job
工作

bank
银行

meeting
会晤，集会，會

office
處，机关，一职

nice to meet you
很高兴认识你

my name is
我名字叫，我叫，我的名字是

what do you do
你是做什么工作的

together
一起

work
某项，见效，干上

hospital
医院

stand
时站，主张，坛

game
游戏，手游，戏

email
电子邮件

understand
会得，体谅，学得

name
取名，名，call

pet
宠物，宠，条狗

phone number
电话号码

sorry
抱歉，内疚，不起

no problem
没问题，没关系

address
地址，住址

know
知道，知不知道，识

cut
划伤，切了，刀割

spanish
西班牙的，西班牙人，西班牙语

but
但别，但，却

year
1年，年，一年

don't
并不，但别，别

language
文，语言，语

do not
不，别，没有

live in
住在

japan
日本

country
国家

do
干上，干吗，搞

bad
坏的，很糟，恶劣

sunny
阳光灿烂，晴朗的，晴

funny
有意思的，逗，好玩的

they're
他们是，她们是，它们是

that
那门，那幅，那枚

little
点，小，少得

love
love，i，疼爱

busy
忙碌的，很忙，很热闹的

dad
父亲，爸爸，我爸

mom
我妈，mom，妈妈

ok
好起来，没关系，还好

always
总是，永远，一直

family
家庭，家族，家

happy
很乐意，欢快，美满

best
最棒的，最出色，最强

friends
guys，老友记，老朋友

here
这里，这儿

where
哪里，从哪里，在哪里

person
者，人比，人

friendly
友好

parent
父母

favorite
最喜欢的，至爱的，最喜爱的

color
颜色，色，色彩

beautiful
美妙，优美的，如画

orange
橘子，橘黄色，橘

dress
连衣裙，裙子，长裙

too
时太，也，过于

really
真的，家真，真令人

song
歌，英语歌，首

pants
皮裤，裤子，裤

shoes
鞋子，鞋，好鞋

one hundred
一百

shoe
鞋子，鞋

cell phone
手机

very
蛮，不得了，极有

very much
非常

that's
那是，那就是，那个是

you're welcome
不客气，不用谢，别客气

key
键，button，关键

bar
bars，横线，吧台

old
旧得，old，陈

except
除，除了，只是

car
车厢，轿车，小轿车

important
重要的

cool
酷，冰凉，炫酷

exact
精确的，确切

questions
题目，问题，题

question
问题，疑问，提问

many
多家，没少，很多都

school
学校，学院

pass
关卡，及格，通没

class
舱，课堂，物理课

glass
玻璃杯，璃，杯

difficult
很难的

that is
那是

has
家有，有床，艾玛有

exam
考试

exams
考试，英语考试

easy
简易，易，容易

today
今天，今日

have
进行，患有，家有

an
一辆，个，一张

these
这几，这，这些

cups of
杯

beers
啤酒

pizzas
比萨

of
给，从，上

cheers
干杯，干，举杯

beer
啤酒，麦酒

goodbye
再见，再会，拜

with
用，配，带

would
将要，会，想

milk
牛奶，奶，牛乳

a cup of
一杯

sugar
糖，白砂糖，白糖

pizza
比萨，披萨，披萨饼

would like
想，要，想要

this is
这是

thank you
谢谢，谢谢你，多谢

welcome to
欢迎到，欢迎来到，欢迎来

restaurant
餐厅，餐馆，火锅店

table
桌子，餐桌，桌

for two
两人用

check
查，查看，查证

menu
菜单，餐单，餐牌

for
为贵，为了，而言

for one
单人用

how old
多大，几岁，多大了

daughter
女儿，闺女，姑娘

five
五，五个，五位

years old
岁，周岁

dear
亲密，亲爱的，贵得

four
四，四个，四位

son
儿子，儿

smart
聪明

life
人生，生命，生活

rich
有钱

tall
个子高，高大，高的

wife
妻子，老婆，太太

husband
丈夫，老公，先生

his
他的，他

girlfriend
女朋友，女友

brother
弟弟，哥哥，兄弟

boyfriend
男朋友，男友

sister
姐姐，妹妹，姊

he's
他，他在，他是

her
她的，她

three
三，3，仨

lots
很多

coats
外套，大衣

two
二，两，2

shirts
衬衫

hats
帽子

how much
多少，多少钱，多少呢

ten
十，10

one
一，1，壹

dollars
美元，元，美圆

much
大，远远，高得

dollar
美元，美金，美圆

sat
坐，SAT

hat
帽子，帽，礼帽

expensive
贵

jacket
夹克，夹衣，套子

need
需要，要，必须

welcome
迎来，客气，欢

bird
鸟儿，禽类，bird

shirt
衬衫

friend
朋友，友人，好友

taxi driver
出租车司机

lock
锁上，锁，门锁

doctor
医生，大夫，医师

oh
哎，噢，呐

bath
泡澡，澡，洗澡

math
数学，算数，算术

chicken
chicken，鸡，鸡肉

cheese
芝士

i'd like
我想要

chair
皮椅，椅，主席

pay
交，掏钱，工资

afternoon
下午，午后

have a nice day
祝你有美好的一天

would you like
你想要，你想要吗，你想不想

sandwich
三明治，三文治，夹心面包

morning
早辰，上午，早

pork
夹猪肉的，猪肉，夹猪肉

salad
沙拉

bye
拜，再见，再会

hi
嗨

please
谢谢，请，劳驾

sea
海边，大海，海

a little
点，一点点，一点

speak
讲个，说话，要说

good
挺不错，很好，不错的

chinese
汉，普通话，华文

land
地落，空地，大地

meat
夹肉，肉类，肉

from
离开，距离，從

nice
亲切，很愉快，很好

new
新来的，新奇，新任

at
in，从，上

excuse me
打扰一下，不好意思，请问

wall
墙壁，面墙，壁

camera
照相机

not
不，不是，并非

wallet
钱包

no
不，没有

watch
照，收看，手表

coat
外套，大衣，上衣

road
道路，马路，山路

thanks
谢谢，感谢，致谢

this
这只，这瓶，这支

by
不迟于，用，之前

bag
皮包，包来，包了

look
毛色，神情，妆容

yes
没错，好，好的

he
他

she
她

woman
女人

are
家有，羊是，排是

man
男人，男子，20

good evening
晚上好

good morning
早上好，早安

a
一辆，个，一款

hello
嗨，哈喽，喂

am
排是，吗，很

girl
女孩子

boy
男孩子

short
矮的，稍微，矮

winter
冬天，冬季，冬日

is
排是，吗，词是

fall
秋天，秋季，秋日

spring
春天，春季，春日

summer
夏天，夏季，夏日

long
長，悠悠，很久

hot
热，烫

less
少点，更少的，更少

or
或，要么，要不然

cold
冷，冰

more
more，大，高得

coffee
咖啡

juice
果汁

water
水，清水，白水

drink
饮品，饮料，喝啤酒

tea
茶，茶水

we
我们

our
我们的

they
他们，她们

their
他们的，她们的

black
黑色，黑，墨色

blue
蓝色，蓝颜色，蓝

white
白色，白，雪白

red
红色，红，赤色

green
绿色，绿，青

computer
电脑，计算机

room
厅，房间，号房

phone
手机，电话，call

big
上大，大，大的

house
房子，房屋，屋子

small
细小，小，迷你的

dog
狗，犬

cat
猫，猫咪

father
爸，神父，父

and
于是，而且，而

mother
我妈，老妈，姆

my
我的，咱的

teacher
教员，师父，指导老师

student
学生

your
你的，您的，你们的

book
书，书籍，书本

Chinese
中文

I
我，咱

English
英文，英语

like
喜欢，喜爱，爱

you
你"""

def parse_words(raw):
    entries = []
    lines = raw.strip().split('\n')
    i = 0
    while i < len(lines):
        word = lines[i].strip()
        if not word:
            i += 1
            continue
        # 下一行是释义
        if i + 1 < len(lines):
            meaning = lines[i + 1].strip()
        else:
            meaning = ''
        # 取释义第一个（逗号前的部分）作为主释义
        meaning_clean = meaning.split('，')[0].split(',')[0].strip()
        entries.append((word, meaning_clean))
        i += 2
        # 跳过空行
        while i < len(lines) and not lines[i].strip():
            i += 1
    return entries

def main():
    if not DB_FILE.exists():
        print(f"❌ 数据库不存在：{DB_FILE}")
        print("   请确认 CiBird 已安装，数据库路径正确")
        return

    entries = parse_words(RAW)
    print(f"📖 解析到 {len(entries)} 个词条")

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row

    # 获取已有单词（避免重复）
    existing = set(row[0].lower() for row in conn.execute("SELECT word FROM words"))
    print(f"📚 词库已有 {len(existing)} 个单词")

    added = 0
    skipped = 0
    for word, meaning in entries:
        if word.lower() in existing:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO words(word, meaning, phonetic, pos, examples, note) VALUES(?,?,?,?,?,?)",
            (word, meaning, '', '', '[]', '')
        )
        existing.add(word.lower())
        added += 1

    conn.commit()
    conn.close()

    print(f"\n✅ 导入完成！")
    print(f"   新增：{added} 个")
    print(f"   跳过（已存在）：{skipped} 个")
    print(f"   词库现有：{len(existing)} 个单词")
    print(f"\n💡 提示：这些单词暂无例句，")
    print(f"   点开任意单词 → 「重新造句」可让 AI 补充例句")

if __name__ == '__main__':
    main()
