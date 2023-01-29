from nonebot import get_driver
# from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters import Message
from nonebot.plugin import on_command
import datetime
from time import strftime
from functools import lru_cache



from .config import Config

global_config = get_driver().config
config = Config.parse_obj(global_config)
LIST = {
"アイビー":"公正と信頼",
"アイビーゼラニウム":"新しいチャレンジ",
"葵":"（一般）豊穣",
#"（白）女性の野心",
"アカシア":"魂の不死",
"アガパンサス":"知的な装い",
"アグリモニー":"多才",
"アゲラタム":"深い信頼",
"朝顔":"（一般）偉大なる友情",
#"（白）喜び溢れ",
"アザミ":"独立",
"アザレア":"（一般）愛で満たされる",
#"（白）節制",
"紫陽花":"移り気",
"アスター":"信じる心",
"アスペン":"自信と勇気",
"アッツ桜":"無意識",
"アネモネ":"（一般）遊び",
#"（赤）君を愛する",
"アベリア":"謙虚",
"アマリリス":"おしゃべり",
"あやめ":"優雅",
"アルストロメリア":"小悪魔的な思い",
"アロエ":"万能",
"杏":"臆病",
"アンスリウム":"強い印象",
"苺":"尊重と愛情",
"イチゴノキ":"あなただけを愛します",
"イベリス":"心を惹きつける",
"インパチェンス":"流れるままに",
"ウィンターグリーン":"際立った個性",
"梅":"澄んだ心",
"エーデルワイス":"尊い記憶",
"エキナセア":"痛みを癒す",
"エビネ":"真実",
"エリカ":"（一般）自立",
#"（クリスマスパレード）沈黙",
"エレモフィラ":"あこがれの人",
"オオイヌノフグリ":"神聖",
"オーク":"（木）強さ",
#"（葉）勇敢さ",
"オシロイバナ":"臆病な愛",
"オステオスペルマム":"心身の健康",
"オダマキ":"（一般）勝利の誓い",
#"（赤）素直",
"オドントグロッサム":"特別な存在",
"オニユリ":"富の蓄積",
"オリーブ":"平和",
"オレンジ":"花嫁の喜び",
"カーネーション":"（一般）神の愛",
#"（ピンク）母の愛",
#"（黄）ユニークな視点",
#"（白）安定",
"ガーベラ":"（一般）神秘的な美しさ",
#"（スパイダー咲）崇高な美しさ",
#"（ピンク）崇高美の探求",
#"（赤）神秘的な魅力",
#"（白）律儀",
#"（オレンジ）続ける力",
#"（黄）究極美",
"楓":"寡黙",
"カキツバタ":"幸運は必ず来る",
"ガザニア":"天才",
"ガジュマル":"沢山の幸せ",
"かすみ草":"夢見心地",
"カタバミ":"光輝く心",
"カトレア":"成熟した大人の魅力",
"ガマズミ":"愛は死より強し",
"カモミール":"逆境に負けぬ強さ",
"カラー":"（色）情熱と勇敢さ",
#"（白）清純さ",
"カランコエ":"幸せを告げる",
"カルミア":"大きな希望",
"カンナ":"情熱と快活",
"カンパニュラ":"高貴",
"桔梗":"変わらぬ愛",
"菊":"（一般）王侯にふさわしい壮麗さ",
#"（うら菊）熟考",
#"（大菊）あなたを心から愛します。",
#"（黄）いつも満たされる",
#"（白）真実を求める",
#"（紅）ダイナミック",
#"（ポンポン咲き）嬉しい夢",
#"（紫紅）社会への愛",
"夾竹桃":"親友",
"金魚草":"世話好き",
"金木犀":"志の高い人",
"銀木犀":"気高い人",
"グズマニア":"あなたは完璧",
"クチナシ":"幸せでとてもうれしい",
"クマツヅラ":"魔法",
"グラジオラス":"準備",
"クリスマスベゴニア":"愛の告白",
"クリスマスローズ":"私の心配をやわらげて",
"クルクマ":"酔いしれる",
"クレマチス":"心の美しさ",
"クロッカス":"天真爛漫",
"クロッサンドラ":"仲良し",
"クローバー":"（一般）私のことを考えて",
#"（四つ葉）望みがかなう",
"黒百合":"独創的",
"グロリオサ":"栄光に満ちた世界",
"ケイトウ":"色褪せぬ恋",
"月下美人":"ただ一度だけ会いたくて",
"月桂樹":"栄光と勝利",
"胡蝶蘭":"幸福が飛んでくる",
"ゴールデンロッド":"用心",
"コスモス":"乙女の心",
"コデマリ":"品格",
"ごぼう":"解放",
"コリアンダー":"秘密の富",
"桜":"精神美",
"さくらんぼ":"真実の心",
"ザクロ":"（花）円熟の美",
#"（実）希望の成就",
"山茶花":"ひたむきに愛します",
"サフラン":"歓喜",
"サボテン":"燃える心",
"百日紅":"雄弁",
"サルビア":"（赤）燃ゆる思い",
#"（紫）尊敬",
"サンセベリア":"永久",
"サンビタリア":"私を見つめて",
"シクラメン":"（一般）はにかみ",
#"（赤）感情の手放し",
#"（ピンク）憧れ",
"杉":"雄大",
"シネラリア":"快活",
"シャクナゲ":"壮厳",
"芍薬":"必ず来る幸福",
"シャコバサボテン":"冒険心",
"ジャスミン":"（アラビアンジャスミン・茉莉花）清浄無垢",
#"（シルクジャスミン・ゲッキツ）正当な道",
#"（一般）愛想の良さ",
#"（マダガスカルジャスミン）私はあなたについていく",
"ジュニパー":"長寿",
"菖蒲（しょうぶ）":"適合",
"ジンジャー":"信頼しています",
"沈丁花":"栄光と不滅",
"シンビジウム":"（白）高貴な人",
#"（ピンク）気取らない心",
"スイートアリッサム":"価値あるもの",
"スイートピー":"私を覚えていて",
"水仙":"自己愛",
"睡蓮":"清純な心",
"スウィートチェストナット":"正当な扱い",
"スカビオサ":"風情",
"杉":"雄大",
"すずらん":"純潔、自然な美しさ",
"スターチス":"永遠に変わらぬ愛",
"ステルンベルギア":"粘り強さ",
"ストック":"（八重咲き）永遠の美",
#"（一重咲き）逆境を克服",
"ストレリチア":"気取った恋",
"スノードロップ":"希望",
"スノーフレーク":"汚れ無き心",
"スミレ":"（青）直観に誠実",
#"（黄）希少価値",
#"（白）無垢",
#"（紫）誠実",
#"（野生）つれづれの恋",
"スモモ":"約束を守って",
"セージ":"家庭の徳",
"セツブンソウ":"光輝",
"ゼラニウム":"（一般）決心",
#"（葉）努力家",
#"（緋）好奇心",
"セントジョーンズワート":"預言者",
"セントポーリア":"小さな愛",
"千日紅":"不滅の愛",
"タイム":"勇気ある行動",
"竹":"高い目標",
"ダリア":"栄華と移り気",
"タンジー":"滅びることのない愛",
"ダンデライオン":"思わせぶり",
"チコリ":"質素",
"茶ノ木":"ユーモア",
"チューブローズ":"危険な楽しみ",
"チューリップ":"（白）観察力",
#"（紫）この世の成功",
#"（黄）名声",
#"（一般）美しい瞳",
#"（赤）永遠の愛",
#"（パーロット咲）愛の表現",
"チョコレートコスモス":"新しい恋のはじまり",
"椿":"（赤）生来の価値",
#"（寒椿）愛嬌",
#"（白椿）愛らしさ",
"露草":"波乱万丈",
"ディアスキア":"私を許して",
"デイジー":"（一般）無邪気",
#"（黄）ありのまま",
#"（白）自由で無邪気",
"デルフィニウム":"変わりやすい心",
"デンドロビウム":"わがままな美人",
"デンファレ":"お似合いの二人",
"トケイソウ":"聖なる愛",
"トリカブト":"致命的なこと",
"トルコキキョウ":"良い語らい",
"トレニア":"魅力と誘惑",
"梨の花":"愛の基盤",
"ナズナ":"私のすべてをあなたに捧げます",
"撫子":"内気",
"菜の花":"前向き",
"ニオイヒバ":"固い友情",
"ニゲラ":"夢の中の恋",
"ニチニチソウ":"楽しい思い出",
"楡":"感受性",
"ネメシア":"偽りのない心",
"ネモフィラ":"愛国心",
"ノウゼンカズラ":"花のある人生",
"ノースポール":"自分に誠実",
"バーベナ":"（一般）家族の和合",
#"（赤）団結",
#"（紫）真実を守る",
#"（ピンク）未来",
"ハイビスカス":"常に新しい美",
"萩":"思案",
"パキラ":"幸運",
"ハクモクレン":"慈悲心",
"バジル":"忍耐力と勇気",
"蓮":"動じない心",
"パセリ":"逆境からの勝利",
"バッカリス":"開拓",
"花菖蒲":"優美",
"花虎ノ尾":"輝かしい実績",
"ハナニラ":"出会い",
"ハナミズキ":"私の思いを受け入れて",
"ハニーサックル":"崇拝",
"パフィオペディラム":"ユニークな視点",
"葉牡丹":"利益",
"薔薇":"（ダマスクローズ）照り映える容色",
#"（蕾）希望、夢",
#"（黒赤色）神秘",
#"（バーガンディー）秘められた美",
#"（白）私はあなたにふさわしい",
#"（ベージュ）成熟した愛",
#"（赤）愛、美",
#"（黄）君のすべてが可憐",
#"（ピンク）愛を誓う",
"ハルジオン":"追憶の愛",
"バレリアン":"善良",
"パンジー":"（一般）私の胸はあなたのことでいっぱいです",
#"（白）温順",
#"（アプリコット）楽しい気分",
#"（紫）愛の使者",
#"（オレンジ）明朗快活",
#"（黄）慎ましい幸せ",
"バンダ":"ユニーク",
"柊":"先見性がある",
"ヒイラギモチ":"清廉",
"ビオラ":"（白）真実に光を当てる",
#"（紫）ゆるぎない魂",
"彼岸花":"思い出",
"ヒソップ":"聖性",
"ビデンス":"美しい調和",
"ひまわり":"（一般）光輝、尊敬",
#"（イタリアンホワイト）あなたを思い続けます。",
"百日草":"遠く離れた友",
"ヒヤシンス":"（青）想像力",
#"（黄）勝負",
#"（白）心静かな愛",
#"（ピンク）スポーツ、ゲーム",
#"（紫）悲哀",
"昼顔":"優しい愛情",
"フィーバーフュー":"不死",
"ブーゲンビリア":"ドラマチックな恋",
"フェンネル":"称賛",
"フクシア":"趣味",
"福寿草":"幸福をつかむ",
"藤の花":"あなたに夢中",
"ブッドレア":"信仰心",
"葡萄":"元気",
"芙蓉":"繊細な美",
"ブラキカム":"自由な美",
"フリージア":"（一般）あどけなさ",
#"（黄）澄んだ心",
"ブリオニア":"幸せの選択",
"プリムラ":"（一般）初恋",
#"（赤）美の秘密",
#"（白）正当",
#"（オブコニカ）少年時代の希望",
#"（ジュリアン）神秘的な心",
#"（ポリアンサ）運命を切り開く",
#"（桜草）若い時代と苦悩",
"ブルーデイジー":"協力的",
"プルメリア":"恵まれた人",
"プルンバゴ":"美意識",
"フロックス":"温和",
"ベゴニア":"好きな人",
"ヘザー":"（赤）頼もしい",
#"（白）追求者",
"ヘーゼル":"和解",
"ペチュニア":"君といると心和む",
"ベラドンナリリー":"美しさ",
"ヘリオトロープ":"献身",
"ペンタス":"希望の実現",
"ポインセチア":"（赤）祝福する",
#"（一般）私の心は燃えている",
#"（白）洞察力",
"鳳仙花":"エネルギッシュ",
"ほおずき":"自然美",
"ポーチュラカ":"チャーミング",
"ボケ":"日々の幸せ",
"牡丹":"富貴",
"ポトス":"永遠の富",
"ポピー":"デリケートな美",
"ボリジ":"才能",
"マーガレット":"（一般）恋の予言",
#"（白）恋の行方",
#"（ピンク）真実の愛",
#"（黄）美しい容姿",
"マロウ":"柔和な心",
"マジョラム":"恥じらい",
"マスタード":"チャレンジと成長",
"松":"不老長寿",
"マドンナリリー":"天界の美",
"マネッチア":"沢山の話",
"マリーゴールド":"太陽",
"マンサク（満作・万作）":"ひらめき",
"ミムラス":"援助の申し出",
"ミモザ（ミモザアカシア）":"秘密の愛",
"ミント":"有徳の人",
"ムスカリ":"黙っていても通じる私の心",
"メドウスイート":"心の支え",
"木蓮":"崇高",
"モミ":"高尚",
"桃":"恋のとりこ",
"モンステラ":"一途な幸せ",
"ヤグルマギク":"天上の人",
"矢車薄荷":"柔らかな心",
"柳":"（一般）従順",
#"（シダレヤナギ）嘆き",
"山吹":"ずっと待っていました",
"ヤロウ":"治癒",
"ユーカリ":"記憶",
"雪割草":"信頼",
"ユーフォルビア":"協力を得る",
"百合":"純粋さ",
"ユリオプスデイジー":"円満",
"夜顔":"夕暮れの思い出",
"ライム":"刺激",
"ライラック":"（一般）私をまだ愛してますか",
#"（白）美しい契り",
"ラナンキュラス":"輝く魅力",
"ラブダナム":"注目",
"ラベンダー":"期待",
"蘭":"勤勉",
"ランタナ":"心変わり",
"リカステ":"汚れなき人",
"リナリア":"私の恋を知って",
"りんご":"偉大",
"リンコスティリス":"大胆",
"リンドウ":"甘い夢",
"ルドベキア":"公平",
"ルバーブ":"忠告",
"ルピナス":"多くの仲間",
"レディースマントル":"ファッション",
"レモン":"愛の忠誠",
"レモンバーベナ":"神聖",
"蝋梅":"慈愛",
"ローズマリー":"あなたは私を蘇らせる",
"ローダンセ":"ロマンチックな愛",
"ロベリア":"いつも可愛らしい",
"ワイルドストロベリー":"徳の成果",
"勿忘草 （忘れな草）":"私を忘れないで",
"吾亦紅（ワレモコウ）":"移り行く日々",
}
hnktb = on_command("花语", aliases = {"hanakotoba", "花言叶", "花言葉"})

def day_hash(day: datetime.date = None) -> int:
    if day is None:
        day = datetime.date.today()
    hash = day.strftime('%y%m%d')
    return int(hash*37)
    
@hnktb.handle()
async def handle_hnktb(message: Message = CommandArg()):
    flower = message.extract_plain_text()
    if flower:
        if flower in LIST:
            send_text = f"「{flower}」の花言葉：{LIST.get(flower)}"
        else:
            send_text = "未找到对应花语：请使用日语！"
    else:
        today_hash = day_hash()
        today_flower = list(LIST.keys())[today_hash % len(LIST)]
        send_text = f"今日花语\n{today_flower}:{LIST.get(today_flower)}"
    send_text = str(send_text)
    await hnktb.send(message=send_text)