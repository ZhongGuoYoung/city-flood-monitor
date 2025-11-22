from datetime import datetime


class Person:
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender


class Student(Person):
    count = 0

    def __init__(self, name, age, gender):
        super().__init__(name, age, gender)
        Student.count += 1
        self.stu_id = f'{datetime.now().year}{Student.count:03d}'
        self.scores = {}

    def add_score(self, subject, score):
        self.scores[subject] = score

    def calcu_avg(self):
        if self.scores:
            return sum(self.scores.values()) / len(self.scores)
        else:
            return 0

    def __str__(self):
        return f'{self.name}({self.age}-{self.gender}).成绩：{self.scores},平均分：{self.calcu_avg()}'


class Manager:
    def __init__(self):
        self.stu_list = []

    def add_student(self):
        name = input("请输入学生的姓名")
        age = int(input("请输入学生的年龄"))
        gender = input("请输入学生的性别")
        stu = Student(name, age, gender)
        self.stu_list.append(stu)
        print(f'添加成功！学号是:{stu.stu_id}')

    def del_student(self):
        sid = input("请输入学号：")
        target = None
        for stu in self.stu_list:
            if sid == stu.stu_id:
                target = stu
        if target:
            self.stu_list.remove(target)
            print("删除成功")
        else:
            print("学号有误，删除失败")

    def show_all_student(self):
        if self.stu_list:
            for stu in self.stu_list:
                print(stu)
        else:
            print("暂无学生")

    def set_score(self):
        sid = input("输入学生学号：")
        for stu in self.stu_list:
            if stu.stu_id == sid:
                score_str = input("请输入学生的成绩(学科-分数，学科-分数）")
                score_list = score_str.replace(',', '，').split('，')
                for item in score_list:
                    subject, score = item.split('-')
                    subject = subject.strip()
                    score = float(score.strip())
                    stu.add_score(subject, score)
                print('添加成功')
                return
        print('添加失败')

    def run(self):
        while True:
            print('***********学号管理************')
            print('1,添加学生')
            print('2,删除学生')
            print('3,查看所有学生')
            print('4,录入成绩')
            print('5,退出')

            chocie = input('请输入操作编号')
            if chocie == '1':
                self.add_student()
            elif chocie == '2':
                self.del_student()
            elif chocie == '3':
                self.show_all_student()
            elif chocie == '4':
                self.set_score()
            elif chocie == '5':
                print('再见')
                break
            else:
                print('输入有误')


m1 = Manager()
m1.run()
