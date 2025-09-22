import os
import sys
import time  # 添加time模块导入
from playwright.sync_api import sync_playwright

# 注释
print("此程序由zyrf-cl开发，仅用以学习交流使用，请勿滥用此软件")
print("使用脚本时请退出正在登录的选课系统，否则会冲突导致程序无法正确运行")
print("1、此脚本可能因校园网站卡顿而报错，只需重新打开即可")
print("2、账号密码输错时重开即可")

# 配置文件读取函数
def load_config():
    """读取配置文件，返回配置字典"""
    config = {
        'username': '',
        'password': '',
        'course_type': '',
        'enable_filter': '',
        'course_name': '',
        'search_interval': 2,
        'click_interval': 0.5,
        'filter_wait': 0.3,
        'page_load_wait': 2,
        'browser_retries': 3,
        'login_retries': 3,
        'enter_course_attempts': 10
    }
    
    config_file = 'config.txt'
    
    # 检查配置文件是否存在
    if not os.path.exists(config_file):
        print(f"未找到配置文件 {config_file}，将使用默认设置")
        return config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"正在读取配置文件: {config_file}")
        
        for line in lines:
            line = line.strip()
            # 跳过注释和空行
            if line.startswith('#') or not line or '=' not in line:
                continue
            
            try:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                if key in config:
                    # 对于数字类型的配置，转换为相应类型
                    if key in ['search_interval', 'click_interval', 'filter_wait', 'page_load_wait']:
                        config[key] = float(value) if value else config[key]
                    elif key in ['browser_retries', 'login_retries', 'enter_course_attempts']:
                        config[key] = int(value) if value else config[key]
                    else:
                        config[key] = value
                        
            except ValueError:
                print(f"配置文件中的行格式错误，跳过: {line}")
                continue
        
        print("✅ 配置文件读取完成")
        return config
        
    except Exception as e:
        print(f"读取配置文件失败: {str(e)}，将使用默认设置")
        return config

# 读取配置
config = load_config()

# 获取用户输入的账号密码（如果配置文件中没有）
if config['username'] and config['password']:
    print(f"使用配置文件中的账号: {config['username']}")
    username = config['username']
    password = config['password']
else:
    print("配置文件中未设置账号密码，请手动输入:")
    username = input("请输入用户名: ")
    password = input("请输入密码: ")

# 获取用户输入
start = input("是否开始抢课？(y/n): ")

# 添加一个通用的等待函数，处理超时和重试
def safe_wait_and_click(locator, timeout=10000, retries=3):
    """安全地等待元素并点击，包含超时和重试机制"""
    for i in range(retries):
        try:
            locator.wait_for(timeout=timeout)
            locator.click()
            return True
        except Exception as e:
            print(f"尝试 {i+1}/{retries} 失败: {str(e)}")
            if i == retries - 1:
                return False
            time.sleep(1)  # 重试前等待1秒
    return False

# 添加统一的过滤器勾选函数
def apply_filters(ciframe, enable_filter=True):
    """统一应用过滤器 - 只处理过滤已满课程，不更改限选和冲突的选择"""
    if not enable_filter:
        print("用户选择不过滤已满课程")
        return
    
    # 只过滤已满课程，不触碰其他过滤器选项
    filter_id = "#sfrm"
    filter_name = "过滤已满课程"
    try:
        # 检查是否已经勾选
        if ciframe.locator(filter_id).is_checked(timeout=2000):
            print(f"✅ {filter_name} 已经勾选，跳过")
            return
        
        ciframe.locator(filter_id).check(timeout=2000)
        print(f"✅ 已勾选: {filter_name}")
    except Exception as e:
        print(f"勾选{filter_name}失败: {str(e)}")
        # 尝试备选定位方案
        try:
            # 专业课备选定位
            alt_locator = "body > div:nth-child(13) > label:nth-child(8) > i"
            ciframe.locator(alt_locator).click(timeout=2000)
            print(f"✅ 使用备选定位成功勾选: {filter_name}")
        except Exception:
            try:
                # 公选课备选定位
                alt_locator = "body > div.search-form-content > div > label:nth-child(8) > i"
                ciframe.locator(alt_locator).click(timeout=2000)
                print(f"✅ 使用备选定位成功勾选: {filter_name}")
            except Exception:
                print(f"❌ 所有定位方式都失败，跳过{filter_name}")

def handle_course_selection(ciframe, course_type="专业课"):
    """处理课程选择的通用函数"""
    # 首先确定是否要过滤已满课程（优先使用配置文件）
    if config['enable_filter'] and config['enable_filter'].lower() in ['y', 'n']:
        filter_choice = config['enable_filter'].lower()
        filter_name = "是" if filter_choice == 'y' else "否"
        print(f"使用配置文件中的过滤设置: {filter_name}")
    else:
        print("配置文件中未设置过滤选项，请手动选择:")
        filter_choice = input("是否要过滤已满课程？(y/n，默认y): ").strip().lower()
    
    if filter_choice == '' or filter_choice == 'y':
        enable_filter = True
        print("✅ 将过滤已满课程")
        # 立即应用过滤器设置
        try:
            apply_filters(ciframe, enable_filter)
            print("✅ 过滤器设置完成")
        except Exception as e:
            print(f"设置过滤器失败: {str(e)}")
    else:
        enable_filter = False
        print("❌ 不过滤已满课程（将显示所有课程包括已满的）")
    
    # 检查配置文件中是否设置了课程名称
    if config['course_name'] and config['course_name'].strip():
        classname = config['course_name'].strip()
        print(f"使用配置文件中的课程名称: {classname}")
        
        # 定位并输入课程名称
        x = ciframe.locator("#kcxx")
        x.fill(classname)
        
        # 根据课程类型选择不同的查询按钮
        if course_type == "专业课":
            query_button = ciframe.locator("body > div:nth-child(13) > input.button")
        else:  # 公选课
            query_button = ciframe.locator('body > div.search-form-content > div > input:nth-child(11)')
        
        print(f"开始自动搜索课程: {classname}")
        print("程序将持续搜索直到选课成功...")
        print("提示：按Ctrl+C可以随时中断自动搜索。")
        
        search_count = 0
        
        # 持续搜索直到成功或用户中断
        while True:
            try:
                search_count += 1
                print(f"第 {search_count} 次搜索...")
                
                # 点击查询按钮
                query_button.click()
                # 等待查询结果 - 使用更灵活的等待策略
                try:
                    # 等待页面加载完成，使用配置的等待时间
                    time.sleep(config['page_load_wait'])  # 使用配置的页面加载等待时间
                    
                    # 尝试等待表格或信息元素出现
                    try:
                        ciframe.wait_for_selector("#dataView", timeout=2000)
                    except:
                        try:
                            ciframe.wait_for_selector("#dataView_info", timeout=2000)
                        except:
                            pass  # 如果都等不到，继续执行检查逻辑
                    
                except Exception as e:
                    print(f"等待页面元素时出现异常: {str(e)}")

                # 判断查询结果 - 使用多种方式检查
                try:
                    # 方式1: 检查dataView_info文本
                    info_text = ""
                    try:
                        info_element = ciframe.locator('#dataView_info')
                        if info_element.count() > 0:
                            info_text = info_element.text_content()
                            print(f"查询信息: {info_text}")
                    except Exception:
                        pass
                    
                    # 方式2: 检查表格中是否有数据行
                    row_count = 0
                    try:
                        table_rows = ciframe.locator("#dataView tbody tr")
                        row_count = table_rows.count()
                        print(f"表格行数: {row_count}")
                    except Exception:
                        pass
                    
                    # 方式3: 检查是否有选课链接（最直接的方式）
                    course_link_count = 0
                    try:
                        if course_type == "专业课":
                            course_links = ciframe.locator("a[href*='xsxkOper']")
                        else:
                            course_links = ciframe.locator("a[href*='xsxkFun']")
                        course_link_count = course_links.count()
                        print(f"找到选课链接数: {course_link_count}")
                    except Exception:
                        pass
                    
                except Exception as e:
                    print(f"检查查询结果时出现异常: {str(e)}，继续重试...")
                    time.sleep(2)
                    continue
                
                # 判断是否有搜索结果 - 使用多个条件
                has_results = False
                
                # 条件1: info文本不为空且不显示0项
                if info_text and "显示 0 至 0 共 0 项" not in info_text and "共 0 项" not in info_text:
                    has_results = True
                    print("✅ 通过info文本检测到搜索结果")
                
                # 条件2: 表格有数据行
                if row_count > 0:
                    has_results = True
                    print("✅ 通过表格行数检测到搜索结果")
                
                # 条件3: 直接找到选课链接
                if course_link_count > 0:
                    has_results = True
                    print("✅ 直接检测到选课链接")
                
                if has_results:
                    print("✅ 查询到数据!")
                    if info_text:
                        print("发现", info_text, "个结果")
                    else:
                        print(f"发现 {row_count} 行数据")
                    print("开始抢课(/≧▽≦)/")

                if has_results:
                    # 简化过滤器检查逻辑，减少延时
                    if enable_filter:
                        try:
                            # 快速检查过滤器状态
                            filter_id = "#sfrm"
                            is_checked = ciframe.locator(filter_id).is_checked(timeout=2000)
                            if not is_checked:
                                print("⚠️ 检测到过滤器被取消，重新应用...")
                                ciframe.locator(filter_id).check(timeout=2000)
                                print("✅ 过滤器已重新勾选")
                                time.sleep(config['filter_wait'])  # 使用配置的过滤器等待时间
                            else:
                                print("ℹ️ 过滤器状态正常")
                        except Exception as e:
                            print(f"过滤器检查失败: {str(e)}")
                    
                    # 查找选课链接 - 根据源码分析优化
                    try:
                        course_links = None
                        numz = 0
                        
                        # 方式1: 查找javascript链接（根据源码分析）
                        if course_type == "专业课":
                            # 查找包含xsxkOper的javascript链接
                            course_links = ciframe.locator("a[href*='xsxkOper']")
                            numz = course_links.count()
                            print(f"专业课：找到 {numz} 个xsxkOper链接")
                        else:  # 公选课
                            # 查找包含xsxkFun的javascript链接
                            course_links = ciframe.locator("a[href*='xsxkFun']")
                            numz = course_links.count()
                            print(f"公选课：找到 {numz} 个xsxkFun链接")
                        
                        # 方式2: 如果没找到javascript链接，查找真正的选课按钮
                        if numz == 0:
                            print("未找到javascript链接，尝试查找真正的选课按钮...")
                            # 只查找真正的选课链接，排除过滤器等干扰元素
                            possible_selectors = [
                                "a:has-text('选课'):not(:has-text('过滤'))",  # 排除包含"过滤"的元素
                                "button:has-text('选课'):not(:has-text('过滤'))",
                                "input[value='选课']",
                                "[onclick*='xsxk']:not(:has-text('过滤'))",
                                "[onclick*='select']:not(:has-text('过滤'))"
                            ]
                            
                            for selector in possible_selectors:
                                try:
                                    course_links = ciframe.locator(selector)
                                    # 进一步验证找到的元素是否为真正的选课链接
                                    valid_links = 0
                                    for i in range(course_links.count()):
                                        try:
                                            text = course_links.nth(i).text_content().strip()
                                            href = course_links.nth(i).get_attribute("href") or ""
                                            onclick = course_links.nth(i).get_attribute("onclick") or ""
                                            
                                            # 排除包含过滤相关文本的元素
                                            if any(keyword in text.lower() for keyword in ["过滤", "限选", "冲突"]):
                                                continue
                                            
                                            # 确保是真正的选课链接
                                            if ("选课" in text and len(text) < 10) or "xsxk" in href or "xsxk" in onclick:
                                                valid_links += 1
                                        except Exception:
                                            continue
                                    
                                    if valid_links > 0:
                                        print(f"使用选择器 '{selector}' 找到 {valid_links} 个有效选课元素")
                                        numz = valid_links
                                        break
                                except Exception:
                                    continue
                        
                        # 方式3: 如果还是没找到，尝试通过表格行查找
                        if numz == 0:
                            print("尝试通过表格行查找选课链接...")
                            try:
                                # 查找表格中的所有链接
                                table_links = ciframe.locator("#dataView tbody tr a")
                                table_link_count = table_links.count()
                                print(f"表格中找到 {table_link_count} 个链接")
                                
                                # 检查每个链接的href属性
                                for i in range(table_link_count):
                                    try:
                                        href = table_links.nth(i).get_attribute("href")
                                        if href and ("xsxk" in href or "select" in href or "选课" in href):
                                            if course_links is None:
                                                course_links = ciframe.locator(f"#dataView tbody tr a").nth(i)
                                                numz = 1
                                            else:
                                                numz += 1
                                            print(f"找到选课链接: {href}")
                                    except Exception:
                                        continue
                                        
                                if numz == 0:
                                    # 最后尝试：查找表格中所有的链接
                                    course_links = table_links
                                    numz = table_link_count
                                    print(f"使用表格中所有链接，共 {numz} 个")
                            except Exception as e:
                                print(f"通过表格查找链接失败: {str(e)}")
                        
                        if numz > 0:
                            print(f"找到 {numz} 个可选课程，立即选课...")
                            # 遍历每个链接并点击
                            click_success_count = 0
                            actual_success_count = 0
                            
                            for i in range(numz):
                                try:
                                    # 获取链接信息用于调试
                                    try:
                                        href = course_links.nth(i).get_attribute("href")
                                        text = course_links.nth(i).text_content().strip()
                                        onclick = course_links.nth(i).get_attribute("onclick") or ""
                                        
                                        # 再次验证这不是过滤器相关的元素
                                        if any(keyword in text.lower() for keyword in ["过滤", "限选", "冲突"]):
                                            print(f"跳过过滤器相关元素: text='{text}'")
                                            continue
                                        
                                        print(f"准备点击第 {i+1} 个链接: href='{href}', text='{text}'")
                                    except Exception:
                                        print(f"准备点击第 {i+1} 个链接")
                                    
                                    # 点击链接
                                    course_links.nth(i).click()
                                    click_success_count += 1
                                    print(f"✅ 已成功点击第 {i+1} 个选课链接")
                                    
                                    # 等待页面响应并检查选课结果
                                    time.sleep(1)  # 等待页面响应
                                    
                                    # 检查是否有弹窗或提示信息
                                    try:
                                        # 检查可能的成功/失败提示
                                        success_indicators = [
                                            "选课成功",
                                            "添加成功", 
                                            "操作成功",
                                            "success"
                                        ]
                                        
                                        failure_indicators = [
                                            "人数已满",
                                            "选课失败",
                                            "已达上限",
                                            "不能选择",
                                            "时间冲突",
                                            "已选过",
                                            "error",
                                            "失败"
                                        ]
                                        
                                        # 检查页面中的提示信息
                                        page_text = ""
                                        try:
                                            # 尝试获取页面文本内容
                                            page_text = ciframe.locator("body").text_content()
                                        except Exception:
                                            pass
                                        
                                        # 检查是否有成功提示
                                        is_success = False
                                        is_failure = False
                                        
                                        for indicator in success_indicators:
                                            if indicator in page_text:
                                                is_success = True
                                                print(f"🎉 检测到成功提示: {indicator}")
                                                break
                                        
                                        for indicator in failure_indicators:
                                            if indicator in page_text:
                                                is_failure = True
                                                print(f"❌ 检测到失败提示: {indicator}")
                                                break
                                        
                                        if is_failure:
                                            print(f"❌ 第 {i+1} 个课程选课失败")
                                        elif is_success:
                                            actual_success_count += 1
                                            print(f"✅ 第 {i+1} 个课程选课成功！")
                                        else:
                                            # 如果没有明确的成功/失败提示，检查课程是否还在列表中
                                            print(f"⚠️ 第 {i+1} 个课程选课结果不明确，需要手动确认")
                                            
                                    except Exception as e:
                                        print(f"检查第 {i+1} 个课程选课结果时出错: {str(e)}")
                                    
                                    time.sleep(config['click_interval'])  # 使用配置的点击间隔
                                    
                                except Exception as e:
                                    print(f"❌ 点击第 {i+1} 个选课链接失败: {str(e)}")
                            
                            # 统计失败数量（在点击过程中已经统计）
                            failure_count = click_success_count - actual_success_count
                            
                            # 根据实际选课结果给出反馈
                            if actual_success_count > 0:
                                print(f"🎉 恭喜恭喜！成功选中 {actual_success_count} 门课程！")
                                print("先别急着关，记得手动点击安全退出")
                                return True  # 真正成功选课，返回
                            elif failure_count > 0:
                                print(f"❌ 选课失败！所有课程因为人数已满或其他原因无法选择")
                                print("继续搜索...")
                                # 不返回，继续搜索
                            elif click_success_count > 0:
                                print(f"⚠️ 已点击 {click_success_count} 个选课链接，但未检测到明确的成功或失败提示")
                                print("请手动检查选课结果")
                                print("继续搜索...")
                                # 不返回，继续搜索
                            else:
                                print("所有选课链接点击都失败，继续搜索...")
                        else:
                            print("虽然查询到数据，但没有找到选课链接，继续搜索...")
                            # 打印页面内容用于调试
                            try:
                                # 打印表格内容
                                table_html = ciframe.locator("#dataView").inner_html()
                                print("表格内容片段:", table_html[:800] + "..." if len(table_html) > 800 else table_html)
                            except Exception:
                                try:
                                    page_content = ciframe.locator("body").inner_html()
                                    print("页面内容片段:", page_content[:500] + "..." if len(page_content) > 500 else page_content)
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"处理选课链接时出现异常: {str(e)}")
                        print("继续搜索...")
                else:
                    # 搜索结果为空，等待2秒后继续搜索
                    print("❌ 暂未搜索到课程，2秒后重新搜索...")
                
                # 等待配置的搜索间隔后继续下一次搜索
                time.sleep(config['search_interval'])
                
            except KeyboardInterrupt:
                print("\n已中断自动搜索模式，切换到手动输入模式。")
                break  # 跳出自动搜索循环，进入手动输入模式
            except Exception as e:
                print(f"搜索过程中出现异常: {str(e)}")
                print("将在2秒后继续搜索同一课程...")
                time.sleep(2)
                # 不要break，继续搜索同一课程
    
    # 手动输入模式
    while True:
        # 输入课程名称
        print("配置文件中未设置课程名称，请手动输入:")
        classname = input("请输入课程名称: ")
        
        # 定位并输入课程名称
        x = ciframe.locator("#kcxx")
        x.fill(classname)
        
        # 根据课程类型选择不同的查询按钮
        if course_type == "专业课":
            query_button = ciframe.locator("body > div:nth-child(13) > input.button")
        else:  # 公选课
            query_button = ciframe.locator('body > div.search-form-content > div > input:nth-child(11)')
        
        print(f"开始搜索课程: {classname}")
        print("如果搜不到课程，将每2秒自动重新搜索...")
        print("提示：按Ctrl+C可以随时中断自动搜索，回到手动输入模式。")
        
        search_count = 0
        
        # 持续搜索直到成功或用户中断
        while True:
            try:
                search_count += 1
                print(f"第 {search_count} 次搜索...")
                
                # 点击查询按钮
                query_button.click()
                # 等待查询结果 - 使用更灵活的等待策略
                try:
                    # 等待页面加载完成，使用配置的等待时间
                    time.sleep(config['page_load_wait'])  # 使用配置的页面加载等待时间
                    
                    # 尝试等待表格或信息元素出现
                    try:
                        ciframe.wait_for_selector("#dataView", timeout=2000)
                    except:
                        try:
                            ciframe.wait_for_selector("#dataView_info", timeout=2000)
                        except:
                            pass  # 如果都等不到，继续执行检查逻辑
                    
                except Exception as e:
                    print(f"等待页面元素时出现异常: {str(e)}")

                # 判断查询结果 - 使用多种方式检查
                try:
                    # 方式1: 检查dataView_info文本
                    info_text = ""
                    try:
                        info_element = ciframe.locator('#dataView_info')
                        if info_element.count() > 0:
                            info_text = info_element.text_content()
                            print(f"查询信息: {info_text}")
                    except Exception:
                        pass
                    
                    # 方式2: 检查表格中是否有数据行
                    row_count = 0
                    try:
                        table_rows = ciframe.locator("#dataView tbody tr")
                        row_count = table_rows.count()
                        print(f"表格行数: {row_count}")
                    except Exception:
                        pass
                    
                    # 方式3: 检查是否有选课链接（最直接的方式）
                    course_link_count = 0
                    try:
                        if course_type == "专业课":
                            course_links = ciframe.locator("a[href*='xsxkOper']")
                        else:
                            course_links = ciframe.locator("a[href*='xsxkFun']")
                        course_link_count = course_links.count()
                        print(f"找到选课链接数: {course_link_count}")
                    except Exception:
                        pass
                    
                except Exception as e:
                    print(f"检查查询结果时出现异常: {str(e)}，继续重试...")
                    time.sleep(2)
                    continue
                
                # 判断是否有搜索结果 - 使用多个条件
                has_results = False
                
                # 条件1: info文本不为空且不显示0项
                if info_text and "显示 0 至 0 共 0 项" not in info_text and "共 0 项" not in info_text:
                    has_results = True
                    print("✅ 通过info文本检测到搜索结果")
                
                # 条件2: 表格有数据行
                if row_count > 0:
                    has_results = True
                    print("✅ 通过表格行数检测到搜索结果")
                
                # 条件3: 直接找到选课链接
                if course_link_count > 0:
                    has_results = True
                    print("✅ 直接检测到选课链接")
                
                if has_results:
                    print("✅ 查询到数据!")
                    if info_text:
                        print("发现", info_text, "个结果")
                    else:
                        print(f"发现 {row_count} 行数据")
                    print("开始抢课(/≧▽≦)/")

                if has_results:
                    # 简化过滤器检查逻辑，减少延时
                    if enable_filter:
                        try:
                            # 快速检查过滤器状态
                            filter_id = "#sfrm"
                            is_checked = ciframe.locator(filter_id).is_checked(timeout=2000)
                            if not is_checked:
                                print("⚠️ 检测到过滤器被取消，重新应用...")
                                ciframe.locator(filter_id).check(timeout=2000)
                                print("✅ 过滤器已重新勾选")
                                time.sleep(config['filter_wait'])  # 使用配置的过滤器等待时间
                            else:
                                print("ℹ️ 过滤器状态正常")
                        except Exception as e:
                            print(f"过滤器检查失败: {str(e)}")
                    
                    # 查找选课链接 - 根据源码分析优化
                    try:
                        course_links = None
                        numz = 0
                        
                        # 方式1: 查找javascript链接（根据源码分析）
                        if course_type == "专业课":
                            # 查找包含xsxkOper的javascript链接
                            course_links = ciframe.locator("a[href*='xsxkOper']")
                            numz = course_links.count()
                            print(f"专业课：找到 {numz} 个xsxkOper链接")
                        else:  # 公选课
                            # 查找包含xsxkFun的javascript链接
                            course_links = ciframe.locator("a[href*='xsxkFun']")
                            numz = course_links.count()
                            print(f"公选课：找到 {numz} 个xsxkFun链接")
                        
                        # 方式2: 如果没找到javascript链接，查找真正的选课按钮
                        if numz == 0:
                            print("未找到javascript链接，尝试查找真正的选课按钮...")
                            # 只查找真正的选课链接，排除过滤器等干扰元素
                            possible_selectors = [
                                "a:has-text('选课'):not(:has-text('过滤'))",  # 排除包含"过滤"的元素
                                "button:has-text('选课'):not(:has-text('过滤'))",
                                "input[value='选课']",
                                "[onclick*='xsxk']:not(:has-text('过滤'))",
                                "[onclick*='select']:not(:has-text('过滤'))"
                            ]
                            
                            for selector in possible_selectors:
                                try:
                                    course_links = ciframe.locator(selector)
                                    # 进一步验证找到的元素是否为真正的选课链接
                                    valid_links = 0
                                    for i in range(course_links.count()):
                                        try:
                                            text = course_links.nth(i).text_content().strip()
                                            href = course_links.nth(i).get_attribute("href") or ""
                                            onclick = course_links.nth(i).get_attribute("onclick") or ""
                                            
                                            # 排除包含过滤相关文本的元素
                                            if any(keyword in text.lower() for keyword in ["过滤", "限选", "冲突"]):
                                                continue
                                            
                                            # 确保是真正的选课链接
                                            if ("选课" in text and len(text) < 10) or "xsxk" in href or "xsxk" in onclick:
                                                valid_links += 1
                                        except Exception:
                                            continue
                                    
                                    if valid_links > 0:
                                        print(f"使用选择器 '{selector}' 找到 {valid_links} 个有效选课元素")
                                        numz = valid_links
                                        break
                                except Exception:
                                    continue
                        
                        # 方式3: 如果还是没找到，尝试通过表格行查找
                        if numz == 0:
                            print("尝试通过表格行查找选课链接...")
                            try:
                                # 查找表格中的所有链接
                                table_links = ciframe.locator("#dataView tbody tr a")
                                table_link_count = table_links.count()
                                print(f"表格中找到 {table_link_count} 个链接")
                                
                                # 检查每个链接的href属性
                                for i in range(table_link_count):
                                    try:
                                        href = table_links.nth(i).get_attribute("href")
                                        if href and ("xsxk" in href or "select" in href or "选课" in href):
                                            if course_links is None:
                                                course_links = ciframe.locator(f"#dataView tbody tr a").nth(i)
                                                numz = 1
                                            else:
                                                numz += 1
                                            print(f"找到选课链接: {href}")
                                    except Exception:
                                        continue
                                        
                                if numz == 0:
                                    # 最后尝试：查找表格中所有的链接
                                    course_links = table_links
                                    numz = table_link_count
                                    print(f"使用表格中所有链接，共 {numz} 个")
                            except Exception as e:
                                print(f"通过表格查找链接失败: {str(e)}")
                        
                        if numz > 0:
                            print(f"找到 {numz} 个可选课程，立即选课...")
                            # 遍历每个链接并点击
                            click_success_count = 0
                            actual_success_count = 0
                            
                            for i in range(numz):
                                try:
                                    # 获取链接信息用于调试
                                    try:
                                        href = course_links.nth(i).get_attribute("href")
                                        text = course_links.nth(i).text_content().strip()
                                        onclick = course_links.nth(i).get_attribute("onclick") or ""
                                        
                                        # 再次验证这不是过滤器相关的元素
                                        if any(keyword in text.lower() for keyword in ["过滤", "限选", "冲突"]):
                                            print(f"跳过过滤器相关元素: text='{text}'")
                                            continue
                                        
                                        print(f"准备点击第 {i+1} 个链接: href='{href}', text='{text}'")
                                    except Exception:
                                        print(f"准备点击第 {i+1} 个链接")
                                    
                                    # 点击链接
                                    course_links.nth(i).click()
                                    click_success_count += 1
                                    print(f"✅ 已成功点击第 {i+1} 个选课链接")
                                    
                                    # 等待页面响应并检查选课结果
                                    time.sleep(1)  # 等待页面响应
                                    
                                    # 检查是否有弹窗或提示信息
                                    try:
                                        # 检查可能的成功/失败提示
                                        success_indicators = [
                                            "选课成功",
                                            "添加成功", 
                                            "操作成功",
                                            "success"
                                        ]
                                        
                                        failure_indicators = [
                                            "人数已满",
                                            "选课失败",
                                            "已达上限",
                                            "不能选择",
                                            "时间冲突",
                                            "已选过",
                                            "error",
                                            "失败"
                                        ]
                                        
                                        # 检查页面中的提示信息
                                        page_text = ""
                                        try:
                                            # 尝试获取页面文本内容
                                            page_text = ciframe.locator("body").text_content()
                                        except Exception:
                                            pass
                                        
                                        # 检查是否有成功提示
                                        is_success = False
                                        is_failure = False
                                        
                                        for indicator in success_indicators:
                                            if indicator in page_text:
                                                is_success = True
                                                print(f"🎉 检测到成功提示: {indicator}")
                                                break
                                        
                                        for indicator in failure_indicators:
                                            if indicator in page_text:
                                                is_failure = True
                                                print(f"❌ 检测到失败提示: {indicator}")
                                                break
                                        
                                        if is_failure:
                                            print(f"❌ 第 {i+1} 个课程选课失败")
                                        elif is_success:
                                            actual_success_count += 1
                                            print(f"✅ 第 {i+1} 个课程选课成功！")
                                        else:
                                            # 如果没有明确的成功/失败提示，检查课程是否还在列表中
                                            print(f"⚠️ 第 {i+1} 个课程选课结果不明确，需要手动确认")
                                            
                                    except Exception as e:
                                        print(f"检查第 {i+1} 个课程选课结果时出错: {str(e)}")
                                    
                                    time.sleep(config['click_interval'])  # 使用配置的点击间隔
                                    
                                except Exception as e:
                                    print(f"❌ 点击第 {i+1} 个选课链接失败: {str(e)}")
                            
                            # 统计失败数量（在点击过程中已经统计）
                            failure_count = click_success_count - actual_success_count
                            
                            # 根据实际选课结果给出反馈
                            if actual_success_count > 0:
                                print(f"🎉 恭喜恭喜！成功选中 {actual_success_count} 门课程！")
                                print("先别急着关，记得手动点击安全退出")
                                return True  # 真正成功选课，返回
                            elif failure_count > 0:
                                print(f"❌ 选课失败！所有课程因为人数已满或其他原因无法选择")
                                print("继续搜索其他课程...")
                                # 不返回，继续搜索
                            elif click_success_count > 0:
                                print(f"⚠️ 已点击 {click_success_count} 个选课链接，但未检测到明确的成功或失败提示")
                                print("请手动检查选课结果")
                                print("继续搜索其他课程...")
                                # 不返回，继续搜索
                            else:
                                print("所有选课链接点击都失败，继续搜索...")
                        else:
                            print("虽然查询到数据，但没有找到选课链接，继续搜索...")
                            # 打印页面内容用于调试
                            try:
                                # 打印表格内容
                                table_html = ciframe.locator("#dataView").inner_html()
                                print("表格内容片段:", table_html[:800] + "..." if len(table_html) > 800 else table_html)
                            except Exception:
                                try:
                                    page_content = ciframe.locator("body").inner_html()
                                    print("页面内容片段:", page_content[:500] + "..." if len(page_content) > 500 else page_content)
                                except Exception:
                                    pass
                    except Exception as e:
                        print(f"处理选课链接时出现异常: {str(e)}")
                        print("继续搜索...")
                else:
                    # 搜索结果为空，等待2秒后继续搜索
                    print("❌ 暂未搜索到课程，2秒后重新搜索...")
                
                # 等待配置的搜索间隔后继续下一次搜索
                time.sleep(config['search_interval'])
                
            except KeyboardInterrupt:
                print("\n已中断自动搜索模式，回到手动输入。")
                # 清空课程名称输入框，回到手动输入模式
                x.fill("")
                break  # 跳出内层循环，回到输入课程名称
            except Exception as e:
                print(f"搜索过程中出现异常: {str(e)}")
                print("将在2秒后继续搜索同一课程...")
                time.sleep(2)
                # 不要break，继续搜索同一课程

def get_browser_path():
    """获取浏览器路径，支持用户自定义"""
    # 常见的Chrome安装路径
    common_chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    ]
    
    # 检查常见路径
    for path in common_chrome_paths:
        if os.path.exists(path):
            print(f"找到浏览器: {path}")
            return path
    
    # 如果没找到，提示用户手动指定
    print("❌ 未找到常见的浏览器安装路径")
    print("常见浏览器路径:")
    for i, path in enumerate(common_chrome_paths, 1):
        print(f"  {i}. {path}")
    
    while True:
        print("\n请选择操作:")
        print("1. 手动输入浏览器完整路径")
        print("2. 使用Playwright内置浏览器（推荐）")
        print("3. 退出程序")
        
        choice = input("请输入选择 (1/2/3): ").strip()
        
        if choice == '1':
            custom_path = input("请输入浏览器完整路径: ").strip().strip('"')
            if os.path.exists(custom_path):
                print(f"✅ 浏览器路径验证成功: {custom_path}")
                return custom_path
            else:
                print(f"❌ 路径不存在: {custom_path}")
                continue
        elif choice == '2':
            print("✅ 将使用Playwright内置浏览器")
            return None  # 返回None表示使用内置浏览器
        elif choice == '3':
            print("程序已退出")
            sys.exit(0)
        else:
            print("❌ 无效选择，请重新输入")

def launch_browser(p, chrome_exe_path):
    """启动浏览器的通用函数"""
    try:
        if chrome_exe_path:
            print(f"使用指定浏览器: {chrome_exe_path}")
            return p.chromium.launch(
                executable_path=chrome_exe_path,
                headless=False,
                slow_mo=100,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
        else:
            print("使用Playwright内置浏览器")
            return p.chromium.launch(
                headless=False,
                slow_mo=100,
                args=[
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage"
                ]
            )
    except Exception as e:
        print(f"❌ 浏览器启动失败: {str(e)}")
        raise e

def login_and_enter_course_system(page, max_retries=3):
    """登录并进入选课系统，支持重试机制"""
    # 如果设置为999，则无限重试
    infinite_retry = (max_retries == 999)
    retry = 0
    
    while True:
        try:
            retry += 1
            if infinite_retry:
                print(f"第 {retry} 次尝试登录... (无限重试模式，按Ctrl+C可终止)")
            else:
                print(f"第 {retry} 次尝试登录...")
            
            # 打开指定网址
            page.goto("https://sso.stu.edu.cn/login?service=http%3A%2F%2Fjw.stu.edu.cn%2F", timeout=60000)
            # 输入用户名
            page.fill("#username", username, timeout=10000)
            # 输入密码
            page.fill("#password", password, timeout=10000)
            # 点击登录按钮
            safe_wait_and_click(page.locator('#login'))

            # 等待页面加载完成
            page.wait_for_load_state("networkidle", timeout=60000)
            
            # 尝试进入选课系统
            print("正在查找选课轮次页面...")
            max_attempts = config['enter_course_attempts']
            infinite_attempts = (max_attempts == 999)
            attempt = 0
            success = False
            
            while True:
                attempt += 1
                try:
                    if infinite_attempts:
                        print(f"第{attempt}次尝试进入选课系统... (无限尝试模式)")
                    else:
                        print(f"第{attempt}次尝试进入选课系统...")
                    
                    # 尝试1: 使用CSS选择器定位蓝色的"进入选课"按钮
                    enter_button = page.locator('button:has-text("进入选课")')
                    if enter_button.is_visible(timeout=1000):
                        print(f"第{attempt}次尝试：点击'进入选课'按钮...")
                        safe_wait_and_click(enter_button)
                        page.wait_for_load_state("networkidle", timeout=60000)
                        
                        # 检查是否成功进入选课系统
                        if page.locator("#Frame0").is_visible(timeout=3000):
                            print("成功进入选课系统！")
                            success = True
                            break
                    
                    # 尝试2: 尝试a标签形式
                    a_button = page.locator('a:has-text("进入选课")')
                    if a_button.is_visible(timeout=1000):
                        print(f"第{attempt}次尝试：点击a标签形式的'进入选课'...")
                        safe_wait_and_click(a_button)
                        page.wait_for_load_state("networkidle", timeout=60000)
                        
                        # 检查是否成功进入选课系统
                        if page.locator("#Frame0").is_visible(timeout=3000):
                            print("成功进入选课系统！")
                            success = True
                            break
                    
                    # 尝试3: 使用更精确的CSS选择器（操作列中的按钮）
                    precise_button = page.locator('td:has-text("操作") + td button:has-text("进入选课")')
                    if precise_button.is_visible(timeout=1000):
                        print(f"第{attempt}次尝试：点击操作列中的'进入选课'按钮...")
                        safe_wait_and_click(precise_button)
                        page.wait_for_load_state("networkidle", timeout=60000)
                        
                        # 检查是否成功进入选课系统
                        if page.locator("#Frame0").is_visible(timeout=3000):
                            print("成功进入选课系统！")
                            success = True
                            break
                    
                    # 尝试4: 检查是否已经在选课系统中
                    if page.locator("#Frame0").is_visible(timeout=2000):
                        print(f"第{attempt}次尝试：已经在选课系统中")
                        success = True
                        break
                    
                    print(f"第{attempt}次尝试：未找到'进入选课'按钮")
                except Exception as e:
                    print(f"第{attempt}次尝试出错: {str(e)}")
                
                # 检查是否达到最大尝试次数
                if not infinite_attempts and attempt >= max_attempts:
                    break
                
                # 每次尝试后等待一段时间再重试
                time.sleep(1)
            
            if success:
                return True
            else:
                if infinite_retry:
                    print(f"第 {retry} 次登录尝试失败，无法进入选课系统，继续重试...")
                    print("等待1秒后重试...")
                    time.sleep(1)
                    continue
                else:
                    print(f"第 {retry} 次登录尝试失败，无法进入选课系统")
                    if retry < max_retries:
                        print("等待1秒后重试...")
                        time.sleep(1)
                        continue
                    else:
                        break
                    
        except KeyboardInterrupt:
            print("\n用户手动终止登录重试")
            return False
        except Exception as e:
            if infinite_retry:
                print(f"第 {retry} 次登录过程中出现异常: {str(e)}，继续重试...")
                print("等待1秒后重试...")
                time.sleep(1)
                continue
            else:
                print(f"第 {retry} 次登录过程中出现异常: {str(e)}")
                if retry < max_retries:
                    print("等待1秒后重试...")
                    time.sleep(1)
                    continue
                else:
                    break
    
    return False

def main():
    if start.lower() != 'y':
        print("程序已退出")
        return
    
    # 获取浏览器路径
    chrome_exe_path = get_browser_path()
    
    # 使用 Playwright
    with sync_playwright() as p:
        browser = None
        max_browser_retries = config['browser_retries']
        infinite_browser_retry = (max_browser_retries == 999)
        browser_retry = 0
        
        while True:
            try:
                browser_retry += 1
                if infinite_browser_retry:
                    print(f"浏览器重试 {browser_retry}: 启动浏览器... (无限重试模式，按Ctrl+C可终止)")
                else:
                    print(f"浏览器重试 {browser_retry}/{max_browser_retries}: 启动浏览器...")
                
                # 启动浏览器
                browser = launch_browser(p, chrome_exe_path)
                page = browser.new_page()
                page.set_default_timeout(60000)
                
                # 尝试登录并进入选课系统
                if login_and_enter_course_system(page, config['login_retries']):
                    break
                else:
                    if infinite_browser_retry:
                        print(f"浏览器重试 {browser_retry}: 登录失败，重启浏览器...")
                        browser.close()
                        browser = None
                        time.sleep(1)
                        continue
                    else:
                        print(f"浏览器重试 {browser_retry}/{max_browser_retries}: 登录失败，重启浏览器...")
                        browser.close()
                        browser = None
                        if browser_retry < max_browser_retries:
                            time.sleep(1)
                            continue
                        else:
                            break
                    
            except KeyboardInterrupt:
                print("\n用户手动终止浏览器重试")
                if browser:
                    try:
                        browser.close()
                    except:
                        pass
                return
            except Exception as e:
                if infinite_browser_retry:
                    print(f"浏览器重试 {browser_retry}: 启动失败 - {str(e)}，继续重试...")
                    if browser:
                        try:
                            browser.close()
                        except:
                            pass
                        browser = None
                    print("等待1秒后重启浏览器...")
                    time.sleep(1)
                    continue
                else:
                    print(f"浏览器重试 {browser_retry}/{max_browser_retries}: 启动失败 - {str(e)}")
                    if browser:
                        try:
                            browser.close()
                        except:
                            pass
                        browser = None
                    
                    if browser_retry < max_browser_retries:
                        print("等待1秒后重启浏览器...")
                        time.sleep(1)
                        continue
                    else:
                        break
        
        if not browser:
            print("❌ 多次重试后仍无法启动浏览器或进入选课系统")
            return
        
        try:

            # 启动弹窗监听器
            def on_dialog(dialog):
                print('Dialog message:', dialog.message)
                dialog.accept()
                print("弹窗已处理")

            page.on('dialog', on_dialog)

            try:
                # 切换到母iframe中点选课中心
                page.frame_locator("#Frame0").locator(
                    'body > div.person > div.person-top > ul > li:nth-child(5)').click()

                # 切换到 父iframe 点击次级选课
                page.frame_locator("#FrameNEW_XSD_PYGL_XKGL_NXSXKZX").locator(
                    "body > div > div.content > div > table > tbody > tr > td:nth-child(4) > span").click()

                # 等待页面加载完成
                page.wait_for_load_state("networkidle")

                # 获取课程类型选择（优先使用配置文件）
                if config['course_type'] and config['course_type'] in ['1', '2']:
                    course_choice = config['course_type']
                    course_name = "专业课" if course_choice == '1' else "公选课"
                    print(f"使用配置文件中的课程类型: {course_name}")
                else:
                    print("配置文件中未设置课程类型，请手动选择:")
                    course_choice = input("选专业课还是公选课？(1：专业课/2：公选课)#只用输入1或2: ")
                
                if course_choice == '1':
                    # 专业课选择
                    # 定位父 iframe
                    aiframe = page.frame_locator("#FrameNEW_XSD_PYGL_XKGL_NXSXKZX")
                    # 定位子 iframe (selectBottom)
                    biframe = aiframe.frame_locator("#selectBottom")
                    # 在子 iframe 内定位元素并点击
                    biframe.locator("body > div.bottom1 > div > ul > li:nth-child(2)").click()
                    # 定位表格 iframe
                    ciframe = biframe.frame_locator("#selectTable")
                    # 处理课程选择（不预先应用过滤器）
                    if handle_course_selection(ciframe, "专业课"):
                        print("专业课选课完成！")
                
                elif course_choice == '2':
                    # 公选课选择
                    # 定位父 iframe
                    aiframe = page.frame_locator("#FrameNEW_XSD_PYGL_XKGL_NXSXKZX")
                    # 定位子 iframe (selectBottom)
                    biframe = aiframe.frame_locator("#selectBottom")
                    # 在子 iframe 内定位元素并点击
                    biframe.locator("body > div.bottom1 > div > ul > li:nth-child(3)").click()
                    # 定位表格 iframe
                    ciframe = biframe.frame_locator("#selectTable")
                    # 处理课程选择（不预先应用过滤器）
                    if handle_course_selection(ciframe, "公选课"):
                        print("公选课选课完成！")
                
                else:
                    print("输入无效，请输入1或2")
                    
            except Exception as e:
                print(f"选课过程中出现异常: {str(e)}")
                # 备用处理逻辑
                try:
                    page.locator('a:has-text("进入选课")').click()
                    page.locator("body > div > div.content > div > table > tbody > tr > td:nth-child(4) > span").click()
                    page.wait_for_load_state("networkidle")
                    
                    # 默认选择公选课
                    biframe = page.frame_locator("#selectBottom")
                    biframe.locator("body > div.bottom1 > div > ul > li:nth-child(3)").click()
                    ciframe = biframe.frame_locator("#selectTable")
                    apply_filters(ciframe)
                    handle_course_selection(ciframe, "公选课")
                    
                except Exception as backup_e:
                    print(f"备用处理也失败: {str(backup_e)}")
                    
        except Exception as e:
            print(f"程序执行过程中出现异常: {str(e)}")
        finally:
            # 等待用户输入，程序不会自动关闭
            input("按 Enter 键退出程序...")
            # 关闭浏览器
            browser.close()

if __name__ == "__main__":
    main()
