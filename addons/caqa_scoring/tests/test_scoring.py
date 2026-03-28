# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError

class TestCaqaScoring(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestCaqaScoring, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Determine the user models for mock testing
        cls.reviewer_1 = cls.env['res.users'].create({
            'name': 'Test Reviewer 1', 'login': 'rev1'
        })
        cls.reviewer_2 = cls.env['res.users'].create({
            'name': 'Test Reviewer 2', 'login': 'rev2'
        })
        
        # Rubric & Levels
        cls.rubric = cls.env.ref('caqa_scoring.default_caqa_rubric_5_point')
        cls.level_5 = cls.env.ref('caqa_scoring.rubric_level_5')
        cls.level_3 = cls.env.ref('caqa_scoring.rubric_level_3')
        cls.level_1 = cls.env.ref('caqa_scoring.rubric_level_1')

        # Mock Standard Environment
        cls.version = cls.env['caqa.standard.version'].create({'name': 'Test V1', 'code': 'V1'})
        cls.chapter = cls.env['caqa.standard.chapter'].create({
            'name': 'Test Chapter 1', 'version_id': cls.version.id, 'sequence': 1
        })
        cls.subchapter = cls.env['caqa.standard.subchapter'].create({
            'name': 'Test Subchapter 1.1', 'chapter_id': cls.chapter.id
        })
        cls.indicator = cls.env['caqa.standard.indicator'].create({
            'name': 'Test Indicator 1.1.1', 'subchapter_id': cls.subchapter.id, 'weight': 10.0
        })

        # Mock Program & Application
        cls.program = cls.env['caqa.program'].create({
            'name': 'Test Program', 'code': 'TP'
        })
        cls.application = cls.env['caqa.application'].create({
            'name': 'Test App', 'program_id': cls.program.id
        })

    def test_01_cycle_generation(self):
        """ Test cycle initiation and automatic score line generation """
        cycle = self.env['caqa.score.cycle'].create({
            'application_id': self.application.id,
            'standard_version_id': self.version.id,
            'reviewer_ids': [(6, 0, [self.reviewer_1.id, self.reviewer_2.id])]
        })
        
        cycle.action_start_progress()
        self.assertEqual(cycle.state, 'in_progress', "Cycle should be in 'in_progress' state.")
        self.assertEqual(len(cycle.line_ids), 2, "Two score lines should be generated (1 per reviewer).")
        
    def test_02_justification_rule(self):
        """ Test that scoring <= 2 requires justification """
        cycle = self.env['caqa.score.cycle'].create({
            'application_id': self.application.id,
            'standard_version_id': self.version.id,
            'reviewer_ids': [(6, 0, [self.reviewer_1.id])]
        })
        cycle.action_start_progress()
        line = cycle.line_ids[0]
        
        # Test 1: Level 1 without justification = ValidationError
        with self.assertRaises(ValidationError):
            line.rubric_level_id = self.level_1.id

        # Test 2: Level 1 with justification = OK
        line.write({
            'rubric_level_id': self.level_1.id,
            'justification': 'Missing significant requirements.'
        })
        self.assertEqual(line.raw_score, 1)
        self.assertEqual(line.weighted_score, 10.0) # 1 * 10 weight

    def test_03_snapshot_immutability(self):
        """ Test that snapshots cannot be altered """
        snapshot = self.env['caqa.score.snapshot'].create({
            'application_id': self.application.id,
            'cycle_id': self.env['caqa.score.cycle'].create({
                'application_id': self.application.id,
                'standard_version_id': self.version.id
            }).id,
            'snapshot_data': '{"test": "data"}'
        })
        
        self.assertTrue(snapshot.checksum)
        with self.assertRaises(ValidationError):
            snapshot.write({'snapshot_data': '{"test": "hacked"}'})
