import json

# from flasgger import swag_from
# from ..swagger.event_dict import *
from . import api_event as blue_print
from flask import jsonify, request
import os
from ..conf import YC_ROOT_URL
import requests

@blue_print.route('/get_base_names', methods=['GET'])
# @swag_from(get_base_names_dict)
def get_base_names():
    res = ["文件标注库", "人员库", "部队库", "地名库", "装备库", "工程库", "机构库", "国家库"]
    return jsonify(res)


@blue_print.route('/search_documents', methods=['GET'])
# @swag_from(search_documents_dict)
def search_documents():
    search = request.args.get('search', '')
    start_date = request.args.get('start_date', '1900-01-01')
    end_date = request.args.get('end_date', '9999-12-31')
    news = [
        {
            "id": "1",
            "name": "荒唐！美国准备在冲绳部署导弹，理由是帮助日本抵御中国“入侵”",
            "create_username": "李密",
            "content": [
                "近日，美军在南海海域频繁对中国挑衅之后，又将目光转移到了驻冲绳美军基地。据美媒报道，美军准备在冲绳附近，部署反舰导弹和防空导弹，理由是帮助日本抵御中国“入侵”，显得十分荒唐可笑。",
                "据美国媒体报道，美国海军陆战队上将、美国海军陆战队第38任司令大卫·伯格表示，未来将向冲绳部署配备反舰和防空导弹的机动部队，以帮助日本应对来自中国的威胁。对此相关专家分析认为，美军打着“帮助日本”的幌子，意图加强冲绳驻日美军的力量。由于驻日美军在冲绳并不受当地居民的待见，美军只好用这种手段进行军事力量扩充。冲绳岛是琉球群岛的第一大岛，而琉球群岛是美国海军构筑第一岛链的地理依托，冲绳岛正好位于第一岛链的中央位置，与美国以关岛基地为核心构建的第二岛链遥相呼应。在防御位置上，呈现出掎角之势，在战时可以互为应援。另外冲绳距离中国钓鱼岛仅440公里，以日本航空自卫队F-15J战斗机的速度，二十多分钟便可到达，所以不管美国还是日本，都非常重视在冲绳的军事力量部署。在冲绳的军事力量中，美国空军和海军陆战队的实力最为强大。美国在小小的冲绳建设有10个左右的空军基地，包括嘉手纳、普天间、那霸等。以嘉手纳空军基地为例，驻扎有美国空军的第18战斗机联队，其下辖三个F-15战斗机中队、一个预警机中队和一个空中加油机中队。装备有F-15战斗机、E-2C鹰眼预警机和P-8I反潜巡逻机等各种作战飞机一百多架。加上驻扎在此地的美国海军第72和第76特混舰队，其配备的鱼叉反舰导弹和标准-2防空导弹，已经完全可以满足美军的反舰和防空作战需求。美国口口声声说部署反舰和防空导弹，是为了帮助日本抵御中国的“入侵”，可是这么多年来，中国始终秉承“与邻为伴，与邻为善”的行为准则，发展与周边邻国的友好关系。反倒是美国，在世界各地，加强军事力量部署，将地区局势军事化、复杂化。美国的这种行为，完全是冷战思维的延续。其通过在全球各地增强军事力量，然后用军事支撑美国的霸权地位。同时借助军事力量，推行强权政治和自己的价值观，维护美国的根本利益，完全不顾世界的和平与安稳。"
            ],
            "path": "标注文档/研究报告",
            "event": {"object": "美国",
                      "event": "准备部署",
                      "subject": "标注-2防空导弹、鱼叉反舰导弹",
                      "start_time": "2020-05-27",
                      "end_time": "2020-05-28"},
            "location": "冲绳:POINT(127.778817850278 26.3857853353472)"
        },
        {
            "id": "2",
            "name": "驻冲绳美军新增60多新冠病例",
            "create_username": "李密",
            "content": [
                "日本冲绳县政府证实，驻扎冲绳的美军相关人员感染新冠病毒人数增多，7日至11日新增61人感染，疫情在基地内部蔓延。美军方面通知冲绳县政府，已封锁两处基地。",
                "冲绳县知事玉城丹尼11日晚召开记者会，证实美军方面通报7日至11日，普天间基地新增确诊38例、汉森营地新增确诊23例。共同社报道，上述两处基地先前已经确诊10例。冲绳县认定基地内部发生聚集性感染，县副知事谢花喜一郎先前要求美方公开感染人数并封锁基地。玉城说：“我对通报内容感到震惊，在冲绳县居民团结一致防范疫情之际，美军相关人员短时间内发生多起感染，实在令人遗憾。让人不得不强烈怀疑美方此前的防疫对策。”除普天间基地和汉森营地，美军驻冲绳嘉手纳基地也有人确诊。7月4日美国独立日前后，美军相关人员在冲绳县内夜店和海滩聚会。冲绳县政府提醒参加过那些聚会的冲绳县居民，身体不适时及时前往医院就诊。2名来自首都圈埼玉县的男子11日在冲绳确诊感染，冲绳县内累计确诊人数升至148人，这一人数不包括美军基地感染病例。"
            ],
            "path": "执勤记录",
            "event": {"object": "驻冲绳美军",
                      "event": "新增",
                      "subject": "新冠病例",
                      "start_time": "2020-06-07",
                      "end_time": "2020-06-11"},
            "location": "冲绳:POINT(127.778817850278 26.3857853353472)"
        },
        {
            "id": "3",
            "name": "冲绳再度爆发反美抗议，高呼赶走美军，大批民众冲击美国军事基地",
            "create_username": "李密",
            "content": [
                "2019年12月31日，日本方面报道称，冲绳地区大批民众再度抗议美军基地。冲绳知事再度要求停止美国基地迁移计划。冲绳县知事再次呼吁日本政府停止有争议的美国空军基地建设计划，该计划遭到了冲绳当地居民的强烈反对，但美国空军基地已在日本南部岛屿上迁移。",
                "而在最新抗议中，大批冲绳民众冲击了美军军营，随后在美日的装甲车到来下，抗议被镇压。对于冲绳县知事呼吁，日本防卫省做出了反应。日本防卫省表示美军在冲绳军事基地的搬迁，该项目所需时间和费用将比早先预计的多一倍以上。日本政府的计划要求将目前位于冲绳繁忙和人口稠密地区的美国海军陆战队，转移到约50公里远的名护市沿海地区。冲绳反对者说，美军基地的搬迁不仅会威胁该地区精致的海洋生态系统，而且还会威胁到其2,000名当地居民。因此，冲绳当地人希望基地完全从冲绳迁出。冲绳当地人玉木告诉记者：“为了尽快关闭和恢复美军普天间航空站，日本必须下令美军这种建设工作应立即停止。”日本防卫省宣布，将普天间军事基地基地迁至汉诺科将耗资85亿美元，历时12年，普天间军事基地的关闭时间推向2030年。根据日本和美国在2013年商定的一项较早计划，新的建设费用约为32亿美元，历时5年，预计将于2022年左右竣工。而最令冲绳人气愤的是，新的美军基地是日本出钱建设的，这是有争议的计划，由于当地人的强烈反对，美军基地撤离呼吁已经推迟了20多年。日本首相安倍晋三政府已发誓要继续扩大美军基地，美军也支持其基地搬迁。东京政府和冲绳当局一直对转移美国基地的计划持反对态度。普天间军事基地搬迁到是美日在1996年首次达成协议的，当时美国军人团伙强奸了一名本地女学生，美国试图平息当地的愤怒，决定搬离了普天间地区。但是长期以来以美国各种借口推脱，搬离基地的计划停滞不前。在今年初冲绳公投中，冲绳县超过70％的选民反对将美国海军陆战队的普天间军事基地迁移和扩张到县内偏远地区。许多冲绳居民将基地与犯罪，污染事故相关联，并希望将美军基地全部撤离该岛。冲绳拥有驻扎在日本的约47,000名美国军事人员中的一半以上人数。根据一项美日双边安全条约，美国基地可以在冲绳使用土地占64％。多年来，美国在冲绳的基地引起了无数抗议和静坐。但是美国就是打压冲绳，就是不从冲绳撤军！"],
            "path": "标注文档/研究报告",
            "event": {"object": "冲绳地区大批民众",
                      "event": "抗议",
                      "subject": "美军基地",
                      "start_time": "2019-12-31",
                      "end_time": "2020-01-01"},
            "location": "冲绳:POINT(127.778817850278 26.3857853353472)"
        },
        {
            "id": "4",
            "name": "盾舰扎堆！日本横须贺海军基地新猛照，水面战力已超越英国和法国",
            "create_username": "张贤",
            "content": [
                "日本网友近日拍摄了一组日本横须贺基地新猛照。位于日本神奈川县横须贺市的横须贺基地，不仅是日本最大的综合性军港，也是驻日美国海军司令部所在地（美国海军第7舰队军港），而且日本海自第1护卫队群第1护卫队的多型主力战舰也驻泊在这里。"],
            "path": "标注文档/执勤记录",
            "event": {"object": "美国海军第7舰队、驻日美国海军司令部、日本海自第1护卫队群第1护卫队的多型主力战舰",
                      "event": "驻泊",
                      "subject": "日本横须贺基地",
                      "start_time": "2020-04-15",
                      "end_time": "2020-04-16"},
            "location": "横须贺:POINT(139.669548030625 35.2845283809028)"
        },
        {
            "id": "5",
            "name": "新一代核潜艇悄悄出港，美航母火速撤往横须贺，日：真正对手来了",
            "create_username": "赵文",
            "content": [
                "据俄罗斯俄新社8月1日报道，8月1日俄罗斯国防部正式宣布，别尔哥罗德号核潜艇开始测试，并在最近已经悄悄出港，进入大洋进行实验性质的航行。而美方在亚太地区的航母获得者消息后，火速返航撤回横须贺海军基地，以防发生意外。",
                "日本方面表示，别尔哥罗德号的出现，使得美方航母碰到了真正的对手。别尔哥罗德号核潜艇的出海之所以引发了西方国家的高度关注，是因为它可以搭载波塞冬号核巡航鱼雷。根据俄罗斯方面的介绍，别尔哥罗德号核潜艇是俄罗斯首个能够搭载核动力波塞冬号核巡航鱼雷的载体，这种潜艇在1992年开始研发，到目前为止已经开始了海试，到年底将会列装俄罗斯海军部队。经过20多年的设计和研发，这种潜艇比设计之初舰体加长了30米，排水量增加到3万吨，成为世界上目前最大的核潜艇。目前这艘潜艇首舰已经制造成功，并于最近下水，低调出海进行海试。仅仅是自身的参数就可以看出来，别尔哥罗德号核潜艇是标准的海底巨无霸，远远超越了一般的核潜艇，因为世界目前主流核潜艇排水量都在1万吨左右，3万吨的排水量意味着可以携带更多的物资和武器，可以在海底续航更长的时间，这样的核潜艇将会具备更好的隐蔽性和更可怕的打击能力。但是别尔哥罗德号核潜艇引发世界关注的不是因为其惊人的排水量，而是因为它是波塞冬核巡航鱼雷的载体。波塞冬核巡航鱼雷这是西方对这款武器的称呼，俄罗斯方面则将其称为核动力无人潜艇，俄罗斯将其称之为潜艇是为了降低其关注度，而西方将其称为核巡航鱼雷则是充分认识到其可怕的打击能力。不管是无人潜艇也好还是巡航鱼雷，波塞冬既可以携带常规弹头也可以携带核弹头，而且因为是无人驾驶而且是核动力，所以理论上这种鱼雷在海底潜航数年，而且在几千米深的还下航行，没有任何设备能够发现其踪影，毕竟发现最大潜深几百米的潜艇都是一件非常困难的事情。而携带核弹头的波塞冬号就像海底的幽灵，可以慢慢接近美方本土，既可以发起对美方基地的打击将其完全摧毁，也可以在海里进行核爆，引发海啸对美方进行攻击，从这个方面看，波塞冬号简直是太可怕了。所以能够携带波塞冬的别尔哥罗德号核潜艇才会如此引发关注，波塞冬核巡航鱼雷一枚重60吨左右，而一艘别尔哥罗德号核潜艇可以搭载4-6个波塞冬。所以俄罗斯尽管没有航母，但是如果出动一艘别尔哥罗德号核潜艇的话，可以击沉数艘航母。"],
            "path": "标注文档/情报信息",
            "event": {"object": "美航母",
                      "event": "火速撤往",
                      "subject": "横须贺",
                      "start_time": "2020-08-01",
                      "end_time": "2020-08-02"},
            "location": "横须贺:POINT(139.669548030625 35.2845283809028)"
        },
        {
            "id": "6",
            "name": "美国“里根”号航母返回横须贺，准航母“美国”号出港进东海活动",
            "create_username": "赵文",
            "content": [
                "“南海战略态势感知计划”官方微博账号在8月1日发布消息称，今天上午，此前在东海活动的美海军“里根”号航母及其属舰返回日本横须贺港口；与此同时，“美国”号两栖攻击舰从佐世保海军基地出港，进入东海活动。",
                "此前在7月30日，该机构官方账号发消息称，7月28日，卫星在奄美群岛西北方向的东海发现美国海军“里根”号航母正向南航行。“里根”号航母7月4日、17日分别在南海参与了两次双航母演习，离开南海后随即与日澳在菲律宾海举行了三边军事演习。5月初，美军官员证实，“里根”号航母已经从日本横须贺舰队基地启航，开展海上试验，这是该舰在新冠病毒大流行期间向海上部署转进的最新一步。自去年11月份结束为期6个月的海上部署返回横须贺舰队基地后，“里根”号一直在开展定期维护。针对美国7月份两次派遣“双航母”赴南海演习，以及美国务院发表涉南海立场文件声明等事件，国防部新闻局副局长、国防部新闻发言人任国强大校在7月30日举行的例行记者会上表示，我们坚决反对美方这个声明。美方罔顾南海问题的历史经纬和客观事实，公然违背美方对南海主权问题不持立场的承诺，肆意无端指责中国、挑拨地区国家关系，派遣“双航母”赴南海演习，这充分暴露美方的“霸权心态”、双重标准。美方以南海问题的所谓“仲裁者”自居，其实就是南海和平的搅局者、地区合作的破坏者、国家关系的挑拨者。中国对于南海诸岛及其附近海域拥有无可争辩的主权，这一点有着充分历史和法理依据。当前，在中国和东盟国家的共同努力下，南海局势总体稳定，相关磋商取得积极进展。我们要求美方停止发表错误言论，停止在南海采取军事挑衅行动，停止对地区国家进行挑拨离间。美方在南海“兴风作浪”只会让中方更加坚定地“乘风破浪”，更加坚定地捍卫自己的主权和安全，更加坚定地维护南海的和平稳定。"],
            "path": "标注文档/情报信息",
            "event": {"object": "美海军“里根”号航母及其属舰",
                      "event": "返回",
                      "subject": "日本横须贺港口",
                      "start_time": "2020-07-30",
                      "end_time": "2020-08-01"},
            "location": "横须贺:POINT(139.669548030625 35.2845283809028)"
        },
        {
            "id": "7",
            "name": "日媒:解放军将举行登陆演习 目标台湾下辖的东沙群岛",
            "create_username": "李密",
            "content": [
                "日本共同社12日发布的一篇独家报道在台湾激起千层浪：“解放军计划在8月举行以‘夺取台湾下辖东沙群岛’为假想目标的登陆演习”。台湾军方当天紧急声明“能确保东沙安全”，岛内专家纷纷猜测解放军此举是“意图打通航母通向太平洋通道”“为南海防空识别区做准备”。",
                "共同社引述消息人士的话称，解放军计划8月在靠近海南岛的南海区域，举行以夺取“台湾下辖东沙群岛”为假想目标的大规模登陆演习。登陆演习将由负责南海防卫的南部战区实施，动用登陆舰、气垫船、直升机和海军陆战队，“规模前所未有”。据介绍，东沙群岛位于从解放军海军设有基地的海南岛经台湾南方的巴士海峡前往太平洋的路线上，对解放军进入太平洋而言具有重要的战略意义。去年12月入列的中国首艘国产航母山东舰也部署在海南岛的基地，“对解放军而言，确实有控制东沙的必要”。此外报道还提到，美军电子战机为收集解放军情报，在东沙附近空域频繁飞行，“仅4月就飞来13次”。报道称，“解放军对美军在南海的军事活动日益活跃感到焦躁，该演习有可能导致与美国、台湾之间的紧张加剧”。台军方面对该报道极为重视。12日上午在台湾“国防部”例行记者会上，台“国防部”发言人史顺文强调，“对周边共军演训与军事动态，国军运用联合情监侦作为，对周遭情况都能充分掌握、及时应处”。目前东沙与太平岛归台湾“海巡署”驻守，驻岛官兵由台海军陆战队负责训练，配备迫击炮、速射机炮等火炮，具有轻装步兵实力。台湾“国防部”作计室联合作战处长林文皇宣称，台军对外离岛都有相关应处机制与应援计划，驻岛部队的战备执勤、火炮射击、战斗技能与后勤维保，相关战备整备工作“具有等同陆战队坚强战力，能确保岛上安全”。台湾《联合报》称，东沙岛的迫击炮阵地隐藏在地表下，“坚固可用”。台“海巡署”12日表示，东沙驻防海巡部队预计6月将实施火力演习，“验证岛上阵地各式迫击炮、机炮射击效能”。除了猜测“解放军夺东沙是意图打通国产航母通往太平洋要道”之外，台湾中正大学战略暨国际事务研究所助理教授林颖佑还认为，解放军这次演习区域跟外界盛传的“南海防空识别区”有部分重叠，因此也可能是为下一步设置“南海防空识别区”做准备。军事专家宋忠平12日对《环球时报》记者表示，东沙群岛处在东南沿海的战略要冲，又连通着南海和西太平洋，位置非常关键。如果东沙群岛由台湾当局租借给美军实施一些军事侦测活动，比如安置侦测器或反潜设备，对解放军的影响较大。台当局已有人主张把太平岛租借给美军，不排除未来租借东沙岛的可能。宋忠平认为，台海局势越发紧张的根本原因在于蔡英文当局不断搞“台独”，甚至要通过制宪的方式来实现法理“台独”。在这种前提下，解放军做好军事斗争准备，包括联合军演，意图“敲山震虎”，警告“台独分子”不要跨越红线和底线。他表示，“解放军的夺岛演练已是常态化科目，夺岛演练顾名思义就是针对岛屿，东沙群岛是岛屿，澎湖列岛也是，台湾本岛是一个更大的岛屿。如果‘台独分子’一意孤行搞分裂，军事演习随时可以转化为军事行动。"],
            "path": "标注文档/情报信息",
            "event": {"object": "解放军",
                      "event": "计划举行",
                      "subject": "以夺取“台湾下辖东沙群岛”为假想目标的大规模登陆演习",
                      "start_time": "2020-08-01",
                      "end_time": "2020-09-01"},
            "location": "东沙群岛:POINT(116.711837035694 20.7082539588889)"
        },
        {
            "id": "8",
            "name": "我国围绕东沙群岛进行登陆演习！巴西人：最危险的军事行动之一！",
            "create_username": "赵文",
            "content": [
                "据环球网5月13日援引日媒报道，我军计划8月在南海举行时长达二个月的演习，以夺取东沙群岛为假象目标进行登陆作战演练，此消息引发国际高度关注。为何巴西人称这是最危险的军事行动之一？报道称，登陆演习将由负责南海防卫的南部战区实施，动用登陆舰、气垫船、直升机以及海军陆战队，规模前所未。",
                "有军事专家对此分析称，东沙群岛具有非常重要的战略意义，在巴士海峡附近，对中国海军进出太平洋是非常重要的战略通道。目前，山东舰部署在海南岛三亚基地，东沙群岛对于整个南海战略的重要性不言而喻。该消息也引发了巴西海军网的关注，该网站综合日媒和中文媒体的消息，详细报道了这次南海演习的一些细节。该报道引发了巴西军事观察人士的热议。",
                "除了关于这次演习的战略意义上的分析，有巴西军事观察人士将分析重点放在的登陆作战。分析指出，两栖登陆战争是最复杂、最危险的军事行动之一。即使防守方数量上处于劣势，但机警、装备精良且准备充分的防守方也会给进攻方造成混乱。",
                "两栖登陆作战按照规模分为战略、战役和战术性登陆作战，按地理条件分为对开阔海岸和岛礁区的登陆作战。",
                "二战时，有多场著名的登陆战役，如著名的诺曼底登陆，虽然盟军取得了最终的胜利，但是战损也不可谓不大。",
                "我军上一次的登陆作战要追溯到1955年1月的解放一江山岛登陆，我军出动一个步兵师，137艘各型军舰，22个航空兵大队，48小时内解决战斗。不过一江山岛只有1.2平方公里，登陆作战规模不大，且距今已有65年，武器装备发生了翻天覆地的变化，因此不具有参考性。",
                "之所以说两栖登陆作战是最危险的军事行动，是因为现代条件下的登陆作战需要海陆空火箭军多军种联合作战，受到自然条件严重影响，强突海区、敌前登陆、背水进攻，战场瞬息万变，协同作战复杂高难。",
                "各种武器装备的火力配置和打击的层次调度也是登陆作战的难点，包括制空权、制海权的争夺，预先的火力覆盖及登陆的扫雷破障，无一不是对作战推进的考验。不过，随着我军的运-20运输机、歼-20隐身战机、海军两栖军舰的大量服役，目前我军登陆作战的立体势态的构建已经达到了全球军事力量中的最顶级水平，目前需要的是各军种之间的协同配合，以期在需要作战的时候，能够快速形成合力，在最短的时间内让敌方失去抵抗能力。东沙群岛行政划分属于广东省汕尾市，面积1.8平方公里，比一江山岛稍大。军事观察人员指出，拿下东沙群岛无须“规模前所未有”的军事演习，按我军现有实力，以及当前东沙群岛山的布防，拿下该岛几乎不太可能遇到有一丁点弹性的反抗。"],
            "path": "标注文档/执勤记录",
            "event": {"object": "计划8月登陆演习",
                      "event": "动用",
                      "subject": "登陆舰、气垫船、直升机以及海军陆战队",
                      "start_time": "2020-08-01",
                      "end_time": "2020-09-01"},
            "location": "东沙群岛:POINT(116.711837035694 20.7082539588889)"
        },
        {
            "id": "9",
            "name": "应对大陆东沙群岛演习，王定宇：已派由美军训练的“九九旅”协防",
            "create_username": "张贤",
            "content": [
                "据外媒报道，大陆本月将在东沙群岛海域进行夺岛演习，民进党籍防务委员会“立委”王定宇向媒体披露，台海军陆战队不但因此派遣加强连协防东沙群岛，台军也做好最坏打算，不排除结合陆军空降特战与陆战队兵力，从南沙太平岛分海空两路打回东沙。",
                "中美持续在南海对峙，传大陆本月将在海南岛军演，模拟夺取东沙岛，王定宇接受台湾《天下》杂志访问，指称台军方也在5月派出有“铁军部队”称号的“九九旅加强连”协防东沙岛，是20年来首见。九九旅是防卫部队，由美军训练，具有反登陆、反空降的能力，“以少搏多是最大特色。”报道同时指出，东沙群岛地势平坦、无险可守，台军也已做好最坏打算，拟定“卫疆作战计划”，一旦大陆直取东沙，海军将派遣特遣舰队，载运海军陆战队一个营的兵力，紧急前往更南边的太平岛，执行武装两栖登陆作战，配合空军C-130运输机载运特战兵力，以空投或战术降落的方式，增援太平岛。王定宇解释，“就是从太平岛打回东沙岛”。台防务防务部门昨天低调表示，针对台湾本岛及南海周边海、空情动态，已透过联合情监侦作为，持续严密掌握，确保“主权”及“领土”安全。"],
            "path": "标注文档/情报信息",
            "event": {"object": "中国大陆",
                      "event": "夺岛演习",
                      "subject": "东沙群岛海域",
                      "start_time": "2020-08-01",
                      "end_time": "2020-09-01"},
            "location": "东沙群岛:POINT(116.711837035694 20.7082539588889)"
        },
        {
            "id": "10",
            "name": "发往南海的“东风快递”：如你所愿，我们是认真的",
            "create_username": "张贤",
            "content": [
                "8月26日，中国向海南岛和西沙群岛之间的南海区域试射东风-26B和东风-21D飞弹，被美媒解读为中国向南海发射“航母杀手”，旨在针对美国。",
                "对此，新晋“肝帝”、观察者网专栏作者沈逸认为，就目前而言，美方飞机抵近侦察之后中国向既定目标发射东风导弹，用这样一种方式，我们传递出了明确的信号，中方的“区域拒止”战略是严肃的、认真的，不是在开玩笑。与此同时，我们相对保持了一种弹性而理性的节奏：第一，有条不紊地应对美方施加的战略压力；第二，清晰地表达中方的战略意志同时准确地展示中方战略性的能力；第三，在涉及关键利益的区位上划出中方能够接受的红线和底线。"],
            "path": "标注文档/情报信息",
            "event": {"object": "中国",
                      "event": "试射",
                      "subject": "东风-26B、东风-21D飞弹",
                      "start_time": "2020-06-15",
                      "end_time": "2020-06-17"},
            "location": "西沙群岛:POINT(111.740308485417 16.2704988929167)"
        }
    ]

    def judge(event_start, event_end):
        if event_start > end_date or event_end < start_date:
            return False
        else:
            return True

    data = [i for i in news
            if judge(i.get("event").get("start_time"), i.get("event").get("end_time"))]
    res = {
        "data": data,
        "page_count": 1,
        "total_count": len(data)
    }

    return jsonify(res)


@blue_print.route('/find_event', methods=['GET'])
# @swag_from(find_event_dict)
def find_event():
    try:
        event_object = request.args.get('object', '')
        event = request.args.get('event', '')
        start_date = request.args.get('start_date', '1900-01-01')
        end_date = request.args.get('end_date', '9999-01-01')
        location = request.args.get('location', '')
        place = location.split(';')[0]

        res = []
        event_mock = os.path.join(os.getcwd(), 'static', 'events-mock.txt')
        with open(event_mock, 'r', encoding="utf-8") as f:
            contents = json.load(f)
            index = 1
            for content in contents:
                if if_match(content, event_object, event, start_date, end_date, place):
                    tmp = {
                        "index": index,
                        "subject": content['subject'],
                        "object": content['object'],
                        "event": content['event'],
                        "start_date": content['start_date'],
                        "end_date": content['end_date'],
                        "place": location
                    }
                    index = index + 1
                    res.append(tmp)
    except Exception as e:
        print(str(e))
        res = []
    print(res)
    return jsonify(res)


def if_match(content, event_object, event, start_date, end_date, place):
    if event_object and event_object != content['subject'] and event_object != content['object']:
        return False
    elif event and event != content['event']:
        return False
    elif end_date < content['start_date'] or start_date > content['end_date']:
        return False
    elif place and place != content['place']:
        return False
    else:
        return True


@blue_print.route('/get_doc_events', methods=['GET'])
# @swag_from(get_doc_events_dict)
def get_doc_events():
    docId = request.args.get('docId', "")
    res = []
    try:
        docId = int(docId.replace('"', ''))
        if YC_ROOT_URL:
            # 雨辰同步
            # header = {"Content-Type": "application/x-form-urlencode; charset=UTF-8"}
            url = YC_ROOT_URL + "/event/listByDocId?docId={0}".format(docId)
            res_result = requests.get(url=url, headers={})
            # print("/event/listByDocId", res_result.text)
            for result in (res_result.json()['data']):
                res.append({
                    "title": result['title'],  # 事件标题
                    "subject": result['eventSubjcet'],  # 事件主语
                    "object": result['eventObject'],  # 事件宾语
                    "datetime": result['eventTime'],  # 发生时间
                    "place": result['eventAddress'],  # 发生地点
                })

        '''
        # 临时测试
        with open(os.path.join(os.getcwd(), 'static', 'get_doc_events.json'), 'r', encoding='utf-8') as f:
            print("read get_doc_events.json")
            res = json.loads(f.read())
        '''
        '''
        # yc接口格式
        [{
            "title": "青岛至连云港以东海域，2020年8月22日1200时至8月26日1200时，在以下5点连线海域内组织重大军事活动",
            "subject": [
                "海事局"
            ],
            "object": null,
            "datetime": [
                "2020-08-22 00:00:00"
            ],
            "place": [
                {
                    "type": 1,
                    "word": "青岛",
                    "placeId": 52245,
                    "placeIon": "120.3778692",
                    "placeLat": "36.06596613"
                },
                {
                    "type": 1,
                    "word": "连云港",
                    "placeId": 52194,
                    "placeIon": "119.21740848",
                    "placeLat": "34.5977166600001"
                }
            ]
        }]
        '''

    except Exception as e:
        print(str(e))

    return jsonify(res)


@blue_print.route('/get_during_events', methods=['GET'])
# @swag_from(get_during_events_dict)
def get_during_events():
    start_date = request.args.get('start_date', "")
    end_date = request.args.get('end_date', "")
    data = []
    if YC_ROOT_URL:
        # 雨辰同步
        header = {"Content-Type": "application/json; charset=UTF-8"}
        url = YC_ROOT_URL + "/event/search"
        body = {"startTime": start_date, "endTime": end_date}
        search_result = requests.post(url, data=json.dumps(body), headers=header)
        # print("/event/listByDocId", search_result.text)
        data = search_result.json()['data']
    res = []
    for item in data:
        res.append({
            "title": item['title'],  # 事件标题
            "subjcet": item['eventSubjcet'],  # 事件主语
            "object": item['eventObject'],  # 事件宾语
            "datetime": item['eventTime'],  # 发生时间
            "address": item['eventAddress']  # 发生地点（字符串，无坐标）

        })
    return jsonify(res)
