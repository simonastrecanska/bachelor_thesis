INSERT INTO template (template_name, template_text)
VALUES
-- MT101
('MT101_Standard_Template', 
'{1:F01BANKBEBBAXXX0000000000}{2:I101BANKDEFFXXXXN}{3:{113:PRIO}}{4:
  BANKBEBBAXXX
  BANKBEBBAXXX
  101
  :20:{message_reference}
  :28D:{sequence_number}/{total_sequences}
  :50H:{ordering_customer_details}
  :52A:{ordering_institution_bic}
  :30:{requested_execution_date}
  :21:{transaction_reference}
  :23E:{instruction_code}
  :32B:{currency}{amount}
  :56A:{intermediary_bic}
  :57A:{beneficiary_institution_bic}
  :59:{beneficiary_account_details}
  :70:{payment_details}
  :71A:{charges}
  }'),

-- MT103
('MT103_Payment_Template',
'{1:F01BANKBEBBAXXX0000000000}{2:I103BANKDEFFXXXXN}{3:{113:PRIO}}{4:
  BANKBEBBAXXX
  BANKBEBBAXXX
  103
  :20:{message_reference}
  :23B:CRED
  :32A:{requested_execution_date}{currency}{amount}
  :33B:{currency}{amount}
  :50K:{ordering_customer_details}
  :52A:{ordering_institution_bic}
  :53B:{sender_correspondent}
  :54A:{receiver_correspondent}
  :59:{beneficiary_account_details}
  :70:{payment_details}
  :71A:{charges}
  }'),

-- MT202
('MT202_Transfer_Template',
'{1:F01BANKBEBBAXXX0000000000}{2:I202BANKDEFFXXXXN}{3:{113:PRIO}}{4:
  :20:{transaction_reference}
  :21:{related_reference}
  :13C:{time_indicator}
  :32A:{execution_date}{currency}{amount}
  :52A:{ordering_institution_bic}
  :53B:{sender_correspondent}
  :54A:{receiver_correspondent}
  :56A:{intermediary_bic}
  :57A:{account_with_institution_bic}
  :58A:{beneficiary_institution_bic}
  :72:{sender_to_receiver_info}
}');
