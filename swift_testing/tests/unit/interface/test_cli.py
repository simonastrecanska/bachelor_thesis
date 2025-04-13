"""
Unit tests for the CLI interface component.

Tests the functionality of the command-line interface for
the SWIFT message routing testing framework.
"""

import pytest
import json
import csv
from io import StringIO
from unittest.mock import patch, MagicMock

from swift_testing.src.interface.cli import (
    setup_arg_parser, handle_generate_command, handle_run_command,
    handle_evaluate_command, handle_list_command, handle_train_command,
    handle_delete_command, main
)


class TestArgParser:
    """Tests for the argument parser setup."""
    
    def test_setup_arg_parser(self):
        """Test that the argument parser is set up correctly."""
        parser = setup_arg_parser()
        
        assert parser is not None
        
        args = parser.parse_args(["--config", "test_config.yaml", "generate", "--name", "TestGeneration", "--num-messages", "10"])
        
        assert args.config == "test_config.yaml"
        assert args.command == "generate"
        assert args.num_messages == 10
        assert args.name == "TestGeneration"
    
    def test_generate_command_args(self):
        """Test the arguments for the generate command."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "generate",
            "--name", "Test Generation",
            "--description", "Test description",
            "--num-messages", "20"
        ])
        
        assert args.command == "generate"
        assert args.num_messages == 20
        assert args.name == "Test Generation"
        assert args.description == "Test description"
    
    def test_run_command_args(self):
        """Test the arguments for the run command."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "--output-format", "json",
            "run",
            "--name", "Test Run",
            "--description", "Test run description"
        ])
        
        assert args.command == "run"
        assert args.name == "Test Run"
        assert args.description == "Test run description"
        assert args.output_format == "json"
    
    def test_evaluate_command_args(self):
        """Test the arguments for the evaluate command."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "--output-format", "json",
            "evaluate",
            "--param-id", "123"
        ])
        
        assert args.command == "evaluate"
        assert args.param_id == 123
        assert args.output_format == "json"
    
    def test_list_command_args(self):
        """Test the arguments for the list command."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "list",
            "--param-id", "123"
        ])
        
        assert args.command == "list"
        assert args.param_id == 123
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "list"
        ])
        
        assert args.command == "list"
        assert args.param_id is None
    
    def test_train_command_args(self):
        """Test the arguments for the train command."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "train",
            "--param-id", "123"
        ])
        
        assert args.command == "train"
        assert args.param_id == 123
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "train"
        ])
        
        assert args.command == "train"
        assert args.param_id is None
    
    def test_delete_command_args(self):
        """Test the arguments for the delete command."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "delete",
            "--param-id", "123"
        ])
        
        assert args.command == "delete"
        assert args.param_id == 123
    
    def test_verbose_arg(self):
        """Test the verbose argument."""
        parser = setup_arg_parser()
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "--verbose",
            "list"
        ])
        
        assert args.verbose is True
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "list"
        ])
        
        assert args.verbose is False
    
    def test_output_format_arg(self):
        """Test the output format argument."""
        parser = setup_arg_parser()
        
        for fmt in ["text", "json", "csv"]:
            args = parser.parse_args([
                "--config", "test_config.yaml",
                "--output-format", fmt,
                "list"
            ])
            
            assert args.output_format == fmt
        
        args = parser.parse_args([
            "--config", "test_config.yaml",
            "list"
        ])
        
        assert args.output_format == "text"


class TestCommandHandlers:
    """Tests for the command handler functions."""
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_generate_command(self, mock_print):
        """Test the generate command handler."""
        mock_framework = MagicMock()
        mock_framework.generate_test_messages.return_value = 123
        
        args = MagicMock()
        args.num_messages = 10
        args.name = "Test Generation"
        args.description = "Test description"
        args.variations_per_template = 3
        args.substitution_rate = 0.2
        args.output_format = "text"
        args.verbose = False
        
        handle_generate_command(args, mock_framework)
        
        mock_framework.generate_test_messages.assert_called_once_with(
            num_messages=10,
            test_name="Test Generation",
            description="Test description",
            variations_per_template=3,
            substitution_rate=0.2
        )
        
        mock_print.assert_called()
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_run_command(self, mock_print):
        """Test the run command handler."""
        mock_framework = MagicMock()
        mock_framework.run_complete_test.return_value = {
            "parameter": {
                "param_id": 123,
                "test_name": "Test Run"
            },
            "num_messages": 50,
            "execution_time": 15.5,
            "accuracy": 0.9,
            "precision": 0.85,
            "recall": 0.88,
            "f1": 0.86,
            "confusion_matrix": [[10, 1], [2, 8]],
            "output_dir": "/path/to/results"
        }
        
        args = MagicMock()
        args.name = "Test Run"
        args.description = "Test description"
        args.num_messages = 50
        args.train = True
        args.output_format = "text"
        args.verbose = False
        
        handle_run_command(args, mock_framework)
        
        mock_framework.run_complete_test.assert_called_once_with(
            "Test Run",
            "Test description",
            50,
            True
        )
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_evaluate_command(self, mock_print):
        """Test the evaluate command handler."""
        mock_framework = MagicMock()
        test_results = {
            "parameter": {
                "param_id": 123,
                "test_name": "Test Parameter"
            },
            "num_messages": 50,
            "accuracy": 0.9,
            "precision": 0.85,
            "recall": 0.88,
            "f1": 0.86,
            "confusion_matrix": [[10, 1], [2, 8]],
            "output_dir": "/path/to/results"
        }
        mock_framework.get_test_results.return_value = test_results
        
        args = MagicMock()
        args.param_id = 123
        args.output_format = "text"
        args.verbose = False
        
        handle_evaluate_command(args, mock_framework)
        
        mock_framework.get_test_results.assert_called_once_with(123)
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_list_command_with_param_id(self, mock_print):
        """Test the list command handler with a specific parameter ID."""
        mock_framework = MagicMock()
        mock_db_manager = MagicMock()
        mock_framework.db_manager = mock_db_manager
        
        parameter_data = {
            "param_id": 123,
            "test_name": "Test Parameter",
            "description": "Test description",
            "creation_date": "2023-01-15 10:30:45"
        }
        mock_db_manager.get_parameter.return_value = parameter_data
        mock_db_manager.get_messages_by_param.return_value = [{"message_id": 1}, {"message_id": 2}]
        
        args = MagicMock()
        args.param_id = 123
        args.output_format = "text"
        args.verbose = False
        
        handle_list_command(args, mock_framework)
        
        mock_db_manager.get_parameter.assert_called_once_with(123)
        mock_db_manager.get_messages_by_param.assert_called_once_with(123)
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_list_command_all_params(self, mock_print):
        """Test the list command handler for all parameters."""
        mock_framework = MagicMock()
        mock_db_manager = MagicMock()
        mock_framework.db_manager = mock_db_manager
        
        parameters_data = [
            {
                "param_id": 123,
                "test_name": "Test Parameter 1",
                "description": "First test parameter",
                "creation_date": "2023-01-15 10:30:45"
            },
            {
                "param_id": 124,
                "test_name": "Test Parameter 2",
                "description": "Second test parameter",
                "creation_date": "2023-01-16 11:20:30"
            }
        ]
        mock_db_manager.execute_query.return_value = parameters_data
        
        args = MagicMock()
        args.param_id = None
        args.output_format = "text"
        args.verbose = False
        
        handle_list_command(args, mock_framework)
        
        expected_sql = "SELECT param_id, test_name, description, creation_date FROM test_parameters ORDER BY param_id DESC"
        mock_db_manager.execute_query.assert_called_once_with(expected_sql)
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_train_command_with_param_id(self, mock_print):
        """Test the train command handler with a specific parameter ID."""
        mock_framework = MagicMock()
        mock_framework.train_model.return_value = {
            "model_id": "model_2023_01_15",
            "accuracy": 0.92,
            "training_time": 45.6,
            "epochs": 10,
            "param_id": 123
        }
        
        args = MagicMock()
        args.param_id = 123
        args.output_format = "text"
        args.verbose = False
        
        handle_train_command(args, mock_framework)
        
        mock_framework.train_model.assert_called_once_with(123)
        
        mock_print.assert_called()
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_train_command_with_templates(self, mock_print):
        """Test the train command handler using templates."""
        mock_framework = MagicMock()
        mock_framework.train_model.return_value = {
            "model_id": "model_2023_01_15",
            "accuracy": 0.92,
            "training_time": 45.6,
            "epochs": 10,
            "param_id": None
        }
        
        args = MagicMock()
        args.param_id = None
        args.output_format = "text"
        args.verbose = False
        
        handle_train_command(args, mock_framework)
        
        mock_framework.train_model.assert_called_once_with(None)
        
        mock_print.assert_called()
    
    @patch("swift_testing.src.interface.cli.print")
    def test_handle_delete_command(self, mock_print):
        """Test the delete command handler."""
        mock_framework = MagicMock()
        mock_db_manager = MagicMock()
        mock_framework.db_manager = mock_db_manager
        
        mock_db_manager.get_parameter.return_value = {
            "param_id": 123,
            "test_name": "Test Parameter"
        }
        
        mock_db_manager.get_messages_by_param.return_value = [
            {"message_id": 1},
            {"message_id": 2}
        ]
        
        args = MagicMock()
        args.param_id = 123
        args.output_format = "text"
        args.verbose = False
        args.confirm = True
        
        handle_delete_command(args, mock_framework)
        
        mock_db_manager.get_parameter.assert_called_once_with(123)
        mock_db_manager.get_messages_by_param.assert_called_once_with(123)
        
        assert mock_db_manager.execute_update.call_count >= 3


class TestOutputFormatting:
    """Tests for the output formatting functionality."""
    
    @patch("swift_testing.src.interface.cli.print")
    def test_text_output_format(self, mock_print):
        """Test the text output format."""
        mock_framework = MagicMock()
        mock_db_manager = MagicMock()
        mock_framework.db_manager = mock_db_manager
        
        mock_db_manager.get_parameter.return_value = {
            "param_id": 123,
            "test_name": "Test Parameter",
            "description": "Test description",
            "creation_date": "2023-01-15 10:30:45"
        }
        
        mock_db_manager.get_messages_by_param.return_value = [
            {"message_id": 1},
            {"message_id": 2}
        ]
        
        args = MagicMock()
        args.param_id = 123
        args.output_format = "text"
        args.verbose = False
        
        handle_list_command(args, mock_framework)
        
        calls = mock_print.call_args_list
        output = "".join(str(call[0][0]) for call in calls if call[0])
        
        assert "Parameter ID: 123" in output
        assert "Test Parameter" in output
        assert "Test description" in output
        assert "2023-01-15 10:30:45" in output
        assert "Messages: 2" in output
    
    @patch("swift_testing.src.interface.cli.print")
    @patch("json.dumps")
    def test_json_output_format(self, mock_json_dumps, mock_print):
        """Test the JSON output format."""
        mock_framework = MagicMock()
        mock_db_manager = MagicMock()
        mock_framework.db_manager = mock_db_manager
        
        parameter_data = {
            "param_id": 123,
            "test_name": "Test Parameter",
            "description": "Test description",
            "creation_date": "2023-01-15 10:30:45"
        }
        mock_db_manager.get_parameter.return_value = parameter_data
        
        expected_data = parameter_data.copy()
        expected_data["message_count"] = 2
        
        mock_db_manager.get_messages_by_param.return_value = [
            {"message_id": 1},
            {"message_id": 2}
        ]
        
        mock_json_dumps.return_value = '{"param_id": 123, "test_name": "Test Parameter", ...}'
        
        args = MagicMock()
        args.param_id = 123
        args.output_format = "json"
        args.verbose = False
        
        handle_list_command(args, mock_framework)
        
        mock_json_dumps.assert_called_once()
        
        called_data = mock_json_dumps.call_args[0][0]
        assert called_data["param_id"] == 123
        assert called_data["test_name"] == "Test Parameter"
        assert called_data["description"] == "Test description"
        assert called_data["message_count"] == 2
    
    @patch("swift_testing.src.interface.cli.print")
    @patch("csv.writer")
    def test_csv_output_format(self, mock_csv_writer, mock_print):
        """Test the CSV output format."""
        mock_framework = MagicMock()
        mock_db_manager = MagicMock()
        mock_framework.db_manager = mock_db_manager
        
        parameters_data = [
            {
                "param_id": 123,
                "test_name": "Test Parameter 1",
                "description": "First test parameter",
                "creation_date": "2023-01-15 10:30:45"
            },
            {
                "param_id": 124,
                "test_name": "Test Parameter 2",
                "description": "Second test parameter",
                "creation_date": "2023-01-16 11:20:30"
            }
        ]
        mock_db_manager.execute_query.return_value = parameters_data
        
        mock_csv_instance = MagicMock()
        mock_csv_writer.return_value = mock_csv_instance
        
        args = MagicMock()
        args.param_id = None
        args.output_format = "csv"
        args.verbose = False
        
        with patch("swift_testing.src.interface.cli.open", create=True) as mock_open:
            mock_file = mock_open.return_value.__enter__.return_value
            handle_list_command(args, mock_framework)
            
            expected_sql = "SELECT param_id, test_name, description, creation_date FROM test_parameters ORDER BY param_id DESC"
            mock_db_manager.execute_query.assert_called_once_with(expected_sql)
            
            mock_open.assert_called_once()
            
            assert mock_csv_writer.called


class TestMainFunction:
    """Tests for the main function."""
    
    @patch("swift_testing.src.interface.cli.create_testing_framework")
    @patch("swift_testing.src.interface.cli.load_config")
    @patch("swift_testing.src.interface.cli.setup_arg_parser")
    def test_main_generate_command(self, mock_setup_parser, mock_load_config, mock_create_framework):
        """Test the main function with the generate command."""
        mock_parser = MagicMock()
        mock_setup_parser.return_value = mock_parser
        
        mock_args = MagicMock()
        mock_args.config = "test_config.yaml"
        mock_args.command = "generate"
        mock_args.verbose = False
        mock_parser.parse_args.return_value = mock_args
        
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_framework = MagicMock()
        mock_create_framework.return_value = mock_framework
        
        with patch("swift_testing.src.interface.cli.handle_generate_command") as mock_handle_generate:
            main()
            mock_handle_generate.assert_called_once_with(mock_args, mock_framework)
    
    @patch("swift_testing.src.interface.cli.create_testing_framework")
    @patch("swift_testing.src.interface.cli.load_config")
    @patch("swift_testing.src.interface.cli.setup_arg_parser")
    def test_main_run_command(self, mock_setup_parser, mock_load_config, mock_create_framework):
        """Test the main function with the run command."""
        mock_parser = MagicMock()
        mock_setup_parser.return_value = mock_parser
        
        mock_args = MagicMock()
        mock_args.config = "test_config.yaml"
        mock_args.command = "run"
        mock_args.verbose = False
        mock_parser.parse_args.return_value = mock_args
        
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_framework = MagicMock()
        mock_create_framework.return_value = mock_framework
        
        with patch("swift_testing.src.interface.cli.handle_run_command") as mock_handle_run:
            main()
            
            mock_handle_run.assert_called_once_with(mock_args, mock_framework)
    
    @patch("swift_testing.src.interface.cli.create_testing_framework")
    @patch("swift_testing.src.interface.cli.load_config")
    @patch("swift_testing.src.interface.cli.setup_arg_parser")
    def test_main_with_verbose(self, mock_setup_parser, mock_load_config, mock_create_framework):
        """Test the main function with the verbose flag."""
        mock_parser = MagicMock()
        mock_setup_parser.return_value = mock_parser
        
        mock_args = MagicMock()
        mock_args.config = "test_config.yaml"
        mock_args.command = "list"
        mock_args.verbose = True
        mock_parser.parse_args.return_value = mock_args

        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        mock_framework = MagicMock()
        mock_create_framework.return_value = mock_framework
        
        with patch("swift_testing.src.interface.cli.logging") as mock_logging:
            main()
            
            mock_logging.basicConfig.assert_called_once()
            args, kwargs = mock_logging.basicConfig.call_args
            assert kwargs.get("level") == mock_logging.DEBUG
    
    @patch("swift_testing.src.interface.cli.create_testing_framework")
    @patch("swift_testing.src.interface.cli.load_config")
    @patch("swift_testing.src.interface.cli.setup_arg_parser")
    @patch("swift_testing.src.interface.cli.logger.error")
    @patch("swift_testing.src.interface.cli.sys.exit")
    def test_main_error_handling(self, mock_exit, mock_error, mock_setup_parser, mock_load_config, mock_create_framework):
        """Test the main function error handling."""
        mock_parser = MagicMock()
        mock_setup_parser.return_value = mock_parser
        
        mock_args = MagicMock()
        mock_args.config = "test_config.yaml"
        mock_args.command = "list"
        mock_args.verbose = False
        mock_parser.parse_args.return_value = mock_args
        
        test_error = Exception("Test error")
        mock_load_config.side_effect = test_error
        
        main()
        
        mock_error.assert_called_once_with(f"Error: {str(test_error)}")
        
        mock_exit.assert_called_once_with(1) 