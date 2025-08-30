#!/usr/bin/env python3
"""
quick_test.py - minimal ASCII-only test for ElderlyBehaviorPredictor
"""

from elderly_behavior_predictor import ElderlyBehaviorPredictor


def quick_test():
    print('quick_test: start')
    try:
        predictor = ElderlyBehaviorPredictor()
        q = predictor.ask_user_checkin_question(speak=False)
        print('Generated question:', q)
        print('quick_test: PASS')
    except Exception as e:
        print('quick_test: FAIL -', e)


if __name__ == '__main__':
    quick_test()
