resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.role_name}_${var.project_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = { Service = "lambda.amazonaws.com" }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  role   = aws_iam_role.lambda_exec_role.id
  policy = var.policy_json
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_exec_role.arn
}
