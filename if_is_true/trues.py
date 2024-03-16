source = input("点数を入力してください。")
source = int(source)
pass_line = 58


if source >= pass_line:
	print("合格です。")
elif source >=(pass_line-20):
	print("後もう少し")

