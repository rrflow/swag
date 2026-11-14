"""The decision contract, layers and server. Software tests with scripted models; not decision quality evidence."""
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib import error, request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import swag_decide as decide
import swag_decision_log
import swag_server
import swag_systemone as contract

BINARY = {'type': 'noul', 'instructions': 'Does this change touch payments?'}
CHOICE = {'type': 'choice', 'instructions': 'Which test layout?', 'criteria': {'a': 'Directories', 'b': 'Groups', 'c': 'Flat'}}
SCORE = {'type': 'score', 'instructions': 'How many CI checks?', 'criteria': ['none', 'one', 'two']}
QUESTIONS = {'risky': BINARY, 'layout': CHOICE, 'ci': SCORE}


def layers(**named):
    return {name: decide.validate_layer(named.get(name)) for name in decide.LAYERS}


def engine_from(fixed):
    """An engine that returns fixed distributions and records what it was asked."""
    calls = []

    def engine(state, questions):
        calls.append({'state': state, 'questions': dict(questions)})
        return {'answers': {key: fixed[key] for key in questions}, 'inputTokens': 3,
                'elapsedMs': {key: 1.0 for key in questions}, 'model': 'fixed', 'protocol': 'test'}
    engine.calls = calls
    return engine


CONFIDENT = {'risky': {'true': 0.9, 'false': 0.1}, 'layout': {'a': 0.7, 'b': 0.2, 'c': 0.1},
             'ci': {'0': 0.1, '1': 0.2, '2': 0.7}}


class ContractTests(unittest.TestCase):
    def test_answers_have_the_shape_systemone_clients_expect(self):
        noul = contract.answer(BINARY, {'true': 0.8, 'false': 0.2})
        self.assertEqual(noul, {'type': 'noul', 'noul': 0.8})
        choice = contract.answer(CHOICE, {'a': 0.7, 'b': 0.2, 'c': 0.1})
        self.assertEqual(choice['choice'], 'a')
        self.assertAlmostEqual(choice['confidence'], (0.7 - 1 / 3) / (1 - 1 / 3), places=5)
        score = contract.answer(SCORE, {'0': 0.1, '1': 0.2, '2': 0.7})
        self.assertAlmostEqual(score['score'], 1.6)
        self.assertEqual(score['legend'], {'0': 'none', '1': 'one', '2': 'two'})
        for question, answer in ((BINARY, noul), (CHOICE, choice), (SCORE, score)):
            back = contract.distribution_from_answer(question, answer)
            self.assertAlmostEqual(math.fsum(back.values()), 1.0)

    def test_confidence_is_zero_when_uniform_and_one_when_certain(self):
        self.assertEqual(contract.choice_confidence([0.25] * 4), 0.0)
        self.assertEqual(contract.choice_confidence([1.0, 0.0, 0.0]), 1.0)
        self.assertEqual(contract.score_confidence([0.0, 1.0, 0.0]), 1.0)
        self.assertAlmostEqual(contract.score_confidence([1 / 3] * 3), 0.0, places=6)

    def test_options_keep_request_order(self):
        self.assertEqual(contract.options(CHOICE), ['a', 'b', 'c'])
        self.assertEqual(contract.options(SCORE), ['0', '1', '2'])
        self.assertEqual(contract.options(BINARY), ['true', 'false'])

    def test_malformed_requests_are_rejected_without_echoing_content(self):
        secret = 'customer-ssn-123'
        for body in (
            [], {'questions': QUESTIONS}, {'state': 'x'}, {'state': 'x', 'questions': {}},
            {'state': 'x', 'questions': {'q': {'type': 'maybe'}}},
            {'state': 'x', 'questions': {'q': {'type': 'choice', 'criteria': {'only': secret}}}},
            {'state': 'x', 'questions': {'q': {'type': 'score', 'criteria': [secret]}}},
            {'state': 'x', 'questions': {'q': {'type': 'noul', 'criteria': {'maybe': secret}}}},
            {'state': 'x', 'questions': {'q': BINARY}, 'extra': secret},
            {'state': 'x', 'questions': {f'q{i}': BINARY for i in range(65)}},
            {'state': 'x', 'questions': {'bad id!': BINARY}},
        ):
            with self.subTest(body=str(body)[:60]), self.assertRaises(contract.ContractError) as caught:
                contract.validate_request(body)
            self.assertNotIn(secret, str(caught.exception))

    def test_engine_distributions_outside_the_options_are_refused(self):
        with self.assertRaises(contract.ContractError):
            contract.check_distribution(CHOICE, {'a': 0.5, 'z': 0.5})
        with self.assertRaises(contract.ContractError):
            contract.check_distribution(CHOICE, {'a': float('nan'), 'b': 0.5, 'c': 0.1})
        with self.assertRaises(contract.ContractError):
            contract.distribution_from_answer(BINARY, {'type': 'noul', 'noul': 1.5})


class LayerTests(unittest.TestCase):
    def run_decide(self, merged_layers, fixed=CONFIDENT, questions=QUESTIONS, suggest=None, today=None):
        engine = engine_from(fixed)
        result = decide.decide({'state': 'request text', 'questions': questions}, merged_layers, engine, suggest, today)
        return result, engine

    def test_all_three_modes_answer_and_raw_probabilities_are_unchanged(self):
        result, _ = self.run_decide(layers())
        decisions = result['swag']['decisions']
        self.assertEqual(decisions['risky']['value'], True)
        self.assertEqual(decisions['layout']['value'], 'a')
        self.assertAlmostEqual(decisions['ci']['value'], 1.6)
        self.assertEqual(decisions['ci']['level'], 2)
        self.assertEqual(result['answers']['layout']['probabilities'], {'a': 0.7, 'b': 0.2, 'c': 0.1})
        self.assertEqual({d['mode'] for d in decisions.values()}, {'binary', 'choice', 'score'})

    def test_abstention_floor_by_type_and_by_question_with_origin(self):
        merged = layers(operator={'preferences': {'abstainBelow': {'choice': 0.9}}},
                        request={'preferences': {'abstainBelow': {'ci': 0.99}}})
        result, _ = self.run_decide(merged)
        layout, ci = result['swag']['decisions']['layout'], result['swag']['decisions']['ci']
        self.assertEqual((layout['status'], layout['reason'], layout['abstainBelowOrigin']),
                         ('abstained', 'below_confidence_floor', 'operator'))
        self.assertEqual((ci['status'], ci['abstainBelowOrigin']), ('abstained', 'request'))
        self.assertEqual(result['swag']['decisions']['risky']['status'], 'answered')

    def test_a_preference_never_goes_below_a_rule_floor(self):
        merged = layers(template={'rules': [{'id': 'careful_layout', 'question': 'layout', 'abstainBelow': 0.9,
                                             'why': 'Layout changes are expensive to undo.'}]},
                        request={'preferences': {'abstainBelow': {'layout': 0.0}}})
        decision = self.run_decide(merged)[0]['swag']['decisions']['layout']
        self.assertEqual(decision['abstainBelow'], 0.9)
        self.assertEqual(decision['abstainBelowOrigin'], 'rule')
        self.assertEqual(decision['status'], 'abstained')

    def test_forbidden_options_are_removed_and_the_rest_renormalized(self):
        merged = layers(project={'rules': [{'id': 'no_dirs', 'question': 'layout', 'forbid': ['a'],
                                            'why': 'The monorepo tooling expects one tree.'}]})
        decision = self.run_decide(merged)[0]['swag']['decisions']['layout']
        self.assertEqual(decision['value'], 'b')
        self.assertAlmostEqual(decision['probability'], 0.2 / 0.3, places=5)
        self.assertEqual(decision['forbidden'], ['a'])
        self.assertEqual(decision['rules'], ['no_dirs'])

    def test_required_answers_belong_to_the_rule_and_skip_the_model(self):
        merged = layers(operator={'rules': [{'id': 'payments_are_risky', 'question': 'risky', 'require': 'true',
                                             'why': 'Every change here can move money.'}]})
        result, engine = self.run_decide(merged)
        decision = result['swag']['decisions']['risky']
        self.assertEqual((decision['status'], decision['value'], decision['reason']), ('required', True, 'hard_rule'))
        self.assertNotIn('risky', engine.calls[0]['questions'])
        self.assertNotIn('risky', result['answers'])

    def test_conflicting_or_impossible_requirements_abstain(self):
        for rules, reason in (
            ([{'id': 'r1', 'question': 'layout', 'require': 'a', 'why': 'x'},
              {'id': 'r2', 'question': 'layout', 'require': 'b', 'why': 'y'}], 'rules_require_different_answers'),
            ([{'id': 'r1', 'question': 'layout', 'require': 'a', 'forbid': ['a'], 'why': 'x'}], 'rule_requires_a_forbidden_option'),
            ([{'id': 'r1', 'question': 'layout', 'require': 'zzz', 'why': 'x'}], 'rule_requires_unknown_option'),
        ):
            with self.subTest(reason=reason):
                decision = self.run_decide(layers(template={'rules': rules}))[0]['swag']['decisions']['layout']
                self.assertEqual((decision['status'], decision['reason']), ('abstained', reason))

    def test_later_layers_cannot_replace_or_weaken_a_rule(self):
        strict = {'id': 'careful', 'question': 'layout', 'abstainBelow': 0.95, 'why': 'Owner decision.'}
        weak = {'id': 'careful', 'question': 'layout', 'abstainBelow': 0.0, 'why': 'Trying to loosen it.'}
        result = self.run_decide(layers(operator={'rules': [strict]}, request={'rules': [weak]}))[0]
        self.assertEqual(result['swag']['decisions']['layout']['status'], 'abstained')
        self.assertEqual(result['swag']['effective']['ruleConflicts'],
                         [{'rule': 'careful', 'layer': 'request', 'kept': 'operator', 'reason': 'rules_cannot_be_replaced'}])

    def test_rule_default_on_abstain_is_marked_as_the_rules(self):
        merged = layers(operator={'rules': [{'id': 'unsure_means_risky', 'question': 'risky', 'onAbstain': 'true',
                                             'why': 'Treat uncertain changes as risky.'}]},
                        request={'preferences': {'abstainBelow': {'risky': 0.99}}})
        decision = self.run_decide(merged)[0]['swag']['decisions']['risky']
        self.assertEqual((decision['status'], decision['value'], decision['defaultedBy']),
                         ('defaulted', True, 'unsure_means_risky'))
        self.assertEqual(decision['abstainReason'], 'below_confidence_floor')

    def test_binary_threshold_preference(self):
        fixed = {**CONFIDENT, 'risky': {'true': 0.3, 'false': 0.7}}
        plain = self.run_decide(layers(), fixed)[0]['swag']['decisions']['risky']
        cautious = self.run_decide(layers(operator={'preferences': {'threshold': {'risky': 0.25}}}), fixed)[0]
        self.assertIs(plain['value'], False)
        self.assertIs(cautious['swag']['decisions']['risky']['value'], True)
        self.assertEqual(cautious['swag']['decisions']['risky']['preferences'][0]['layer'], 'operator')
        # A threshold of zero still cannot pick a side a rule forbids.
        forbidding = layers(template={'rules': [{'id': 'never_true', 'question': 'risky', 'forbid': ['true'], 'why': 'x'}]},
                            request={'preferences': {'threshold': {'risky': 0.0}}})
        self.assertIs(self.run_decide(forbidding, fixed)[0]['swag']['decisions']['risky']['value'], False)

    def test_preferred_option_wins_only_a_near_tie(self):
        near = {**CONFIDENT, 'layout': {'a': 0.46, 'b': 0.44, 'c': 0.10}}
        merged = layers(project={'preferences': {'prefer': {'layout': ['b']}}})
        decision = self.run_decide(merged, near)[0]['swag']['decisions']['layout']
        self.assertEqual(decision['value'], 'b')
        self.assertEqual(decision['preferences'][0]['reason'], 'near_tie')
        clear = self.run_decide(merged)[0]['swag']['decisions']['layout']
        self.assertEqual(clear['value'], 'a')
        self.assertEqual(clear['preferences'], [])

    def test_fresh_facts_reach_the_model_and_stale_facts_do_not(self):
        facts = [{'id': 'uses_stripe', 'statement': 'The project bills through Stripe.', 'source': 'package.json',
                  'observedAt': '2026-11-01', 'freshForDays': 30},
                 {'id': 'old_ci', 'statement': 'CI runs on Travis.', 'source': 'operator',
                  'observedAt': '2025-01-01', 'freshForDays': 30}]
        rules = [{'id': 'stripe_risky', 'question': 'risky', 'whenFact': 'uses_stripe', 'require': 'true', 'why': 'Money.'},
                 {'id': 'travis_layout', 'question': 'layout', 'whenFact': 'old_ci', 'forbid': ['a'], 'why': 'Old CI.'}]
        result, engine = self.run_decide(layers(project={'facts': facts, 'rules': rules}), today=date(2026, 11, 14))
        self.assertEqual(engine.calls[0]['state'], {'request': 'request text', 'facts': ['The project bills through Stripe.']})
        self.assertEqual([f['id'] for f in result['swag']['effective']['staleFacts']], ['old_ci'])
        self.assertEqual(result['swag']['decisions']['risky']['status'], 'required')
        layout = result['swag']['decisions']['layout']
        self.assertEqual(layout['value'], 'a')
        self.assertEqual(layout['skippedRules'], [{'rule': 'travis_layout', 'reason': 'fact_missing_or_stale', 'fact': 'old_ci'}])

    def test_suggestions_follow_decisions_rules_first_and_respect_the_limit(self):
        suggest = {'layout': {'a': 'Split into directories.', 'abstain': 'Share the test layout.'},
                   'risky': {'true': 'Add an idempotency key.'}, 'ci': {'2': 'Add type checking.'}}
        merged = layers(operator={'rules': [{'id': 'payments', 'question': 'risky', 'require': 'true', 'why': 'Money.'}],
                                  'preferences': {'suggestionLimit': 2}})
        rows = self.run_decide(merged, suggest=suggest)[0]['swag']['suggestions']
        self.assertEqual([(row['question'], row['byRule']) for row in rows], [('risky', True), ('layout', False)])

    def test_without_an_engine_only_rules_decide(self):
        merged = layers(operator={'rules': [{'id': 'payments', 'question': 'risky', 'require': 'true', 'why': 'Money.'}]})
        result = decide.decide({'state': 'x', 'questions': QUESTIONS}, merged, None)
        statuses = {key: (value['status'], value.get('reason')) for key, value in result['swag']['decisions'].items()}
        self.assertEqual(statuses, {'risky': ('required', 'hard_rule'), 'layout': ('abstained', 'no_engine'),
                                    'ci': ('abstained', 'no_engine')})
        self.assertFalse(result['swag']['engine']['consulted'])
        # A rule's safe default still applies with no model, and never to a forbidden option.
        merged = layers(operator={'rules': [{'id': 'safe_layout', 'question': 'layout', 'onAbstain': 'b', 'why': 'x'}]})
        layout = decide.decide({'state': 'x', 'questions': QUESTIONS}, merged, None)['swag']['decisions']['layout']
        self.assertEqual((layout['status'], layout['value'], layout['abstainReason']), ('defaulted', 'b', 'no_engine'))

    def test_invalid_layers_are_refused(self):
        for layer in ({'preferences': {'mood': 'happy'}}, {'rules': [{'id': 'x', 'question': 'q', 'why': 'no effect'}]},
                      {'rules': [{'id': 'x', 'question': 'q', 'why': 'w', 'abstainBelow': 2}]},
                      {'facts': [{'id': 'f', 'statement': 's', 'source': 'x', 'freshForDays': 3}]},
                      {'unknown': []}):
            with self.subTest(layer=layer), self.assertRaises(decide.LayerError):
                decide.validate_layer(layer)

    def test_shipped_operator_preferences_are_executable(self):
        layer = decide.operator_layer()
        self.assertTrue(layer['preferences']['abstainBelow'])
        self.assertEqual(layer['rules'], [])


class ScriptedChat(BaseHTTPRequestHandler):
    """An OpenAI-compatible model that always favours the label shown first, to expose order bias."""

    def log_message(self, *arguments):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.server.requests.append(body)
        options = body['messages'][1]['content'].split('Options:\n')[1].splitlines()
        top = [{'token': line[0], 'logprob': -0.1 if index == 0 else -3.0} for index, line in enumerate(options)]
        encoded = json.dumps({'choices': [{'logprobs': {'content': [{'token': top[0]['token'], 'top_logprobs': top}]}}],
                              'usage': {'prompt_tokens': 5}}).encode()
        self.send_response(200)
        self.send_header('Content-Length', str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class ServerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.model = ThreadingHTTPServer(('127.0.0.1', 0), ScriptedChat)
        self.model.requests = []
        threading.Thread(target=self.model.serve_forever, daemon=True).start()
        self.addCleanup(self.model.server_close)
        self.addCleanup(self.model.shutdown)
        self.environment = patch.dict(os.environ, {
            'SWAG_DECISION_MODEL_CONNECTION_FILE': str(self.connect()),
            'SWAG_DECISION_LOG': str(self.directory / 'log.jsonl'),
            'SWAG_TRACE_DIR': str(self.directory / 'traces'),
        })
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def connect(self, rotations=False):
        (self.directory / 'model.env').write_text('MODEL_KEY=test-credential-value\n')
        path = self.directory / 'connection.json'
        path.write_text(json.dumps({
            'schemaVersion': 1, 'baseUrl': f'http://127.0.0.1:{self.model.server_address[1]}', 'model': 'scripted',
            'protocol': 'chat_first_token', 'credentialFile': 'model.env', 'credentialVariable': 'MODEL_KEY',
            'rotations': rotations, 'timeoutMs': 10000, 'maxRequestBytes': 1000000, 'maxResponseBytes': 1000000}))
        return path

    def start(self, token=None):
        server = swag_server.serve('127.0.0.1', 0, None, token)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return f'http://127.0.0.1:{server.server_address[1]}'

    def call(self, url, path, body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = 'Bearer ' + token
        data = None if body is None else json.dumps(body).encode()
        try:
            with request.urlopen(request.Request(url + path, data=data, headers=headers), timeout=10) as response:
                return response.status, json.loads(response.read())
        except error.HTTPError as failure:
            return failure.code, json.loads(failure.read())

    def test_a_systemone_client_gets_answers_and_the_decision_is_logged(self):
        url = self.start()
        status, body = self.call(url, '/v1/systemone', {'model': 'swag', 'state': 'add stripe checkout', 'questions': QUESTIONS})
        self.assertEqual(status, 200)
        self.assertEqual(set(body['answers']), set(QUESTIONS))
        self.assertEqual(body['answers']['risky']['type'], 'noul')
        self.assertEqual(body['swag']['engine']['protocol'], 'chat_first_token')
        self.assertEqual(len(self.model.requests), 3)
        status, log = self.call(url, '/v1/decisions?limit=5')
        self.assertEqual((status, log['requests']), (200, 1))
        record = log['records'][0]
        self.assertNotIn('add stripe checkout', json.dumps(record))
        self.assertEqual(set(record['questions']), set(QUESTIONS))
        self.assertIn('engineMs', record['timings'])

    def test_rotations_cancel_a_model_that_always_picks_the_first_label(self):
        os.environ['SWAG_DECISION_MODEL_CONNECTION_FILE'] = str(self.connect(rotations=True))
        body = swag_server.run({'state': 'x', 'questions': {'layout': CHOICE}}, log=False)
        probabilities = body['answers']['layout']['probabilities']
        # Without rotation 'a' would win every time. Offsets 0 and 1 disagree, so offset 2 is added:
        # each option is shown first once and the bias cancels.
        self.assertLess(max(probabilities.values()) - min(probabilities.values()), 1e-6)
        self.assertEqual(len(self.model.requests), 3)

    def test_templates_supply_questions_layers_and_suggestions(self):
        body = swag_server.run({'state': 'pyproject.toml lists pytest under dependencies', 'swag': {'template': 'python_delivery_review'}},
                               log=False)
        self.assertEqual(set(body['swag']['decisions']), {'dependency_separation', 'test_organization', 'ci_check_coverage'})
        self.assertEqual({d['mode'] for d in body['swag']['decisions'].values()}, {'binary', 'choice', 'score'})
        self.assertEqual(body['swag']['effective']['preferenceOrigins']['abstainBelow.noul'], 'operator')

    def test_errors_are_plain_and_never_leak_internals(self):
        url = self.start()
        status, body = self.call(url, '/v1/systemone', {'state': 'x', 'questions': {'q': {'type': 'maybe'}}})
        self.assertEqual(status, 422)
        self.assertNotIn('Traceback', json.dumps(body))
        status, body = self.call(url, '/v1/systemone', {'state': 'x', 'questions': QUESTIONS, 'swag': {'execute': True}})
        self.assertEqual(status, 422)
        status, body = self.call(url, '/v1/systemone', {'state': 'x', 'questions': QUESTIONS, 'swag': {'template': '../x'}})
        self.assertEqual(status, 422)

    def test_a_token_is_required_beyond_loopback_and_enforced_when_set(self):
        with self.assertRaises(SystemExit):
            swag_server.serve('0.0.0.0', 0, None, None)
        url = self.start(token='s3cret')
        self.assertEqual(self.call(url, '/v1/systemone', {'state': 'x', 'questions': QUESTIONS})[0], 401)
        self.assertEqual(self.call(url, '/v1/decisions')[0], 401)
        self.assertEqual(self.call(url, '/v1/systemone', {'state': 'x', 'questions': QUESTIONS}, token='wrong')[0], 401)
        self.assertEqual(self.call(url, '/v1/systemone', {'state': 'x', 'questions': QUESTIONS}, token='s3cret')[0], 200)
        self.assertEqual(self.call(url, '/health')[0], 200)

    def test_project_layer_comes_from_the_repo(self):
        repo = self.directory / 'repo'
        (repo / '.swag').mkdir(parents=True)
        (repo / '.swag' / 'layer.json').write_text(json.dumps({'rules': [
            {'id': 'payments', 'question': 'risky', 'require': 'true', 'why': 'This project moves money.'}]}))
        body = swag_server.run({'state': 'x', 'questions': QUESTIONS}, repo, log=False)
        self.assertEqual(body['swag']['decisions']['risky']['status'], 'required')
        self.assertEqual(body['swag']['effective']['rules'][0]['layer'], 'project')

    def test_log_summary_counts_statuses_and_hops(self):
        swag_server.run({'state': 'x', 'questions': QUESTIONS})
        swag_server.run({'state': 'y', 'questions': QUESTIONS, 'swag': {'preferences': {'abstainBelow': {'choice': 1.0}}}})
        summary = swag_decision_log.read()
        self.assertEqual(summary['requests'], 2)
        self.assertEqual(summary['byMode']['choice'], {'answered': 1, 'abstained': 1})
        self.assertEqual(summary['hopsMs']['engineMs']['samples'], 2)


class LegacyPreviewEndpointTests(unittest.TestCase):
    """The older /v1/decision preview service must not spend model credit or leak internals over HTTP."""

    def test_execution_flags_are_refused_and_failures_are_plain(self):
        import swag_decision_service

        class Failing:
            calls = 0

            def decide(self, payload):
                Failing.calls += 1
                raise RuntimeError('internal detail /home/someone/secret.py')

        handler = type('Handler', (swag_decision_service.Handler,), {'service': Failing()})
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f'http://127.0.0.1:{server.server_address[1]}/v1/decision'
        for body, expected in (({'intent_text': 'x', 'execute_frontier': True}, 403),
                               ({'intent_text': 'x', 'execute_local': True}, 403),
                               ({'intent_text': 'x'}, 400)):
            with self.subTest(body=body):
                req = request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
                with self.assertRaises(error.HTTPError) as caught:
                    request.urlopen(req, timeout=10)
                text = caught.exception.read().decode()
                self.assertEqual(caught.exception.code, expected)
                self.assertNotIn('internal detail', text)
                self.assertNotIn('Traceback', text)
        self.assertEqual(Failing.calls, 1)


if __name__ == '__main__':
    unittest.main()
