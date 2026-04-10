import logging; logging.basicConfig(level=logging.INFO); from agents.preprocess import run as p_run; from agents.ocr import run as o_run; from agents.translate import run as t_run
state1 = {'image_path': 'test_images/test_english_1.png', 'retry_count':0, 'lang':''}
state1 = p_run(state1); state1 = o_run(state1); state1 = t_run(state1)
print('Final 1:', state1.get('final_text'))
state2 = {'image_path': 'test_images/test_tamil_1.png', 'retry_count':0, 'lang':''}
state2 = p_run(state2); state2 = o_run(state2); state2 = t_run(state2)
print('Final 2:', state2.get('final_text'))
