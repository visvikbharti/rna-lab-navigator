"""
Management command to create a test evaluation set with sample questions.
"""

import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from api.models import EvaluationSet, ReferenceQuestion


class Command(BaseCommand):
    help = 'Creates a test evaluation set with sample questions for RNA Lab Navigator'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            default='Test Evaluation Set',
            help='Name for the evaluation set'
        )
        
        parser.add_argument(
            '--description',
            default='A test evaluation set with sample RNA biology questions',
            help='Description for the evaluation set'
        )
    
    def handle(self, *args, **options):
        name = options['name']
        description = options['description']
        
        # Check if an evaluation set with this name already exists
        if EvaluationSet.objects.filter(name=name).exists():
            self.stdout.write(self.style.WARNING(
                f'An evaluation set named "{name}" already exists. Skipping creation.'
            ))
            return
        
        # Create the evaluation set
        eval_set = EvaluationSet.objects.create(
            name=name,
            description=description,
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(
            f'Created evaluation set: "{name}" (ID: {eval_set.id})'
        ))
        
        # Sample questions for RNA biology
        sample_questions = [
            {
                "question_text": "What buffer composition is used in RNA extraction protocols?",
                "question_type": "factoid",
                "expected_answer": "RNA extraction protocols typically use buffers containing guanidinium thiocyanate, which is a chaotropic agent that denatures proteins, including RNases. Common buffer components include phenol, chloroform, and isoamyl alcohol for phase separation. TRIzol reagent, a commonly used solution, contains phenol and guanidinium isothiocyanate.",
                "expected_sources": [
                    {"title": "protocol_RNAextraction.pdf", "doc_type": "protocol"}
                ],
                "doc_type": "protocol",
                "difficulty": 1
            },
            {
                "question_text": "What are the key steps in qPCR quantification?",
                "question_type": "procedure",
                "expected_answer": "The key steps in qPCR quantification include: 1) Sample preparation and RNA extraction, 2) cDNA synthesis through reverse transcription, 3) PCR amplification with fluorescent reporters, 4) Data collection during the exponential phase, 5) Analysis using either absolute quantification with a standard curve or relative quantification with reference genes, 6) Calculation of threshold cycle (Ct) values, and 7) Interpretation of results with appropriate controls.",
                "expected_sources": [
                    {"title": "qPCR_Quant_Protocol_Guide_11322363_A.pdf", "doc_type": "protocol"}
                ],
                "doc_type": "protocol",
                "difficulty": 2
            },
            {
                "question_text": "How does CRISPR-Cas13 differ from CRISPR-Cas9?",
                "question_type": "comparison",
                "expected_answer": "CRISPR-Cas13 differs from CRISPR-Cas9 in several key ways: 1) Cas13 targets RNA while Cas9 targets DNA, 2) Cas13 has collateral RNase activity that cleaves nearby non-targeted RNAs upon target recognition, 3) Cas13 recognizes a PRRA motif instead of the PAM sequence in Cas9, 4) Cas13 utilizes crRNA with a direct repeat structure different from Cas9's guide RNA, and 5) Cas13 has applications in RNA knockdown, RNA editing, and diagnostics, while Cas9 is primarily used for genome editing.",
                "expected_sources": [
                    {"title": "2021_Kumar_BiosensBioelectron_Precision_SNV_CasDiagnostics.pdf", "doc_type": "paper"}
                ],
                "doc_type": "paper",
                "difficulty": 3
            },
            {
                "question_text": "What is the mechanism of action of the RNA editing enzyme ADAR?",
                "question_type": "explanation",
                "expected_answer": "ADAR (Adenosine Deaminase Acting on RNA) enzymes catalyze the deamination of adenosine to inosine in double-stranded RNA. This A-to-I editing changes the base-pairing properties, as inosine is recognized as guanosine by cellular machinery. The mechanism involves: 1) ADAR binding to dsRNA via double-stranded RNA binding domains (dsRBDs), 2) Recognition of the target adenosine in a specific sequence context, 3) Flipping the adenosine into the catalytic pocket, 4) Hydrolytic deamination at the C6 position of adenosine, removing the amino group, and 5) Formation of inosine, which alters the RNA sequence and can affect splicing, translation, and RNA structure.",
                "expected_sources": [],
                "doc_type": "",
                "difficulty": 4
            },
            {
                "question_text": "What troubleshooting steps should be taken if RNA yield is low during extraction?",
                "question_type": "context",
                "expected_answer": "When RNA yield is low during extraction, consider these troubleshooting steps: 1) Check starting material quality and quantity, 2) Ensure proper sample homogenization, 3) Verify reagent quality and storage conditions, 4) Extend the lysis step, 5) Optimize the precipitation step with carrier molecules like glycogen, 6) Reduce sample loss during washes, 7) Check for RNase contamination, 8) Ensure proper temperature control throughout the protocol, 9) Use fresh reagents, especially phenol-based solutions which can oxidize over time, and 10) Consider using a specialized RNA extraction kit for difficult samples.",
                "expected_sources": [
                    {"title": "common_rna_issues.md", "doc_type": "troubleshooting"}
                ],
                "doc_type": "troubleshooting",
                "difficulty": 2
            }
        ]
        
        # Add questions to the evaluation set
        questions_created = 0
        for q_data in sample_questions:
            ReferenceQuestion.objects.create(
                evaluation_set=eval_set,
                **q_data
            )
            questions_created += 1
        
        self.stdout.write(self.style.SUCCESS(
            f'Added {questions_created} questions to the evaluation set'
        ))
        
        self.stdout.write(self.style.SUCCESS(
            f'Test evaluation set created successfully. Use the evaluation system to test the RAG pipeline.'
        ))