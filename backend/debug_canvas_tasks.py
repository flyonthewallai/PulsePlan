"""
Debug script to test Canvas task creation for specific courses
"""
import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.jobs.canvas.backfill_job import get_canvas_backfill_job

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

USER_ID = "4dd1cef4-a1e9-4b34-a711-1a1e17adbd83"

async def test_specific_course_processing():
    """Test processing assignments from a specific course"""
    try:
        from datetime import datetime
        backfill_job = get_canvas_backfill_job()

        # Get unprocessed assignments from staging - try to find future ones
        response = backfill_job.supabase.table("assignment_import").select("*").eq(
            "user_id", USER_ID
        ).eq("processed", False).execute()  # Get all assignments

        staging_assignments = response.data or []
        logger.info(f"Found {len(staging_assignments)} assignments to test")

        # Group assignments by course to analyze filtering
        courses_stats = {}
        successful_tasks = []
        failed_conversions = []
        past_assignments_filtered = []

        from datetime import timezone
        current_time = datetime.utcnow().replace(tzinfo=timezone.utc)
        logger.info(f"Current time for filtering: {current_time}")

        for staging_assignment in staging_assignments:
            try:
                assignment_data = staging_assignment["raw_payload"]
                canvas_id = staging_assignment["canvas_id"]
                assignment_name = assignment_data.get("name", "Unknown")
                course_name = assignment_data.get("course", {}).get("name", "Unknown Course")
                due_at = assignment_data.get("due_at")

                # Track course stats
                if course_name not in courses_stats:
                    courses_stats[course_name] = {
                        "total": 0,
                        "past_filtered": 0,
                        "successful": 0,
                        "failed": 0
                    }
                courses_stats[course_name]["total"] += 1

                logger.info(f"Testing assignment: '{assignment_name}' from course '{course_name}' (Canvas ID: {canvas_id})")
                if due_at:
                    logger.info(f"  Due date: {due_at}")

                # Convert to TaskModel
                task = await backfill_job._convert_assignment_to_task(USER_ID, assignment_data)

                if task:
                    logger.info(f"✅ Successfully converted: {assignment_name}")
                    task_dict = task.to_supabase_insert()
                    logger.debug(f"Task dict keys: {list(task_dict.keys())}")
                    logger.debug(f"External source: {task_dict.get('external_source')}")
                    logger.debug(f"External ID: {task_dict.get('external_id')}")
                    successful_tasks.append((task_dict, course_name))
                    courses_stats[course_name]["successful"] += 1
                else:
                    logger.warning(f"❌ Task conversion returned None: {assignment_name}")
                    failed_conversions.append((assignment_name, course_name))

                    # Check if this was filtered due to past date
                    if due_at:
                        from dateutil import parser
                        try:
                            due_date = parser.isoparse(due_at.replace('Z', '+00:00'))
                            if due_date < current_time:
                                logger.info(f"  → Likely filtered as past assignment (due {due_date})")
                                past_assignments_filtered.append((assignment_name, course_name, due_date))
                                courses_stats[course_name]["past_filtered"] += 1
                            else:
                                logger.warning(f"  → Should be future assignment but still filtered! Due {due_date}")
                                courses_stats[course_name]["failed"] += 1
                        except Exception as date_e:
                            logger.error(f"  → Date parsing failed: {date_e}")
                            courses_stats[course_name]["failed"] += 1
                    else:
                        logger.warning(f"  → No due date provided")
                        courses_stats[course_name]["failed"] += 1

            except Exception as e:
                logger.error(f"❌ Error converting '{assignment_name}': {e}")
                failed_conversions.append((f"{assignment_name}: {str(e)}", course_name))

        # Test database insertion for successful tasks
        if successful_tasks:
            logger.info(f"\n🔍 Testing database insertion for {len(successful_tasks)} tasks")
            try:
                # Test inserting just one task first
                test_task = successful_tasks[0][0]  # Get task dict from tuple
                logger.info(f"Testing single task insertion: {test_task.get('title')}")

                result = backfill_job.supabase.table("tasks").upsert(
                    [test_task],
                    on_conflict="user_id,external_source,external_id"
                ).execute()

                logger.info(f"✅ Successfully inserted single task: {result.data}")

                # Now test batch insertion
                if len(successful_tasks) > 1:
                    logger.info(f"Testing batch insertion of {len(successful_tasks)} tasks")
                    task_dicts = [task[0] for task in successful_tasks]  # Extract task dicts
                    result = backfill_job.supabase.table("tasks").upsert(
                        task_dicts,
                        on_conflict="user_id,external_source,external_id"
                    ).execute()

                    logger.info(f"✅ Successfully inserted batch: {len(result.data if result.data else [])} tasks")

            except Exception as e:
                logger.error(f"❌ Database insertion failed: {e}")
                logger.error(f"Failed task sample: {test_task}")

        # Course-by-course breakdown
        logger.info(f"\n📊 Course-by-Course Analysis:")
        for course_name, stats in courses_stats.items():
            logger.info(f"\n  {course_name}:")
            logger.info(f"    - Total assignments: {stats['total']}")
            logger.info(f"    - Past filtered: {stats['past_filtered']}")
            logger.info(f"    - Successfully converted: {stats['successful']}")
            logger.info(f"    - Failed conversions: {stats['failed']}")

        # Overall Summary
        logger.info(f"\n📊 Overall Summary:")
        logger.info(f"  - Total assignments analyzed: {len(staging_assignments)}")
        logger.info(f"  - Successful conversions: {len(successful_tasks)}")
        logger.info(f"  - Past assignments filtered: {len(past_assignments_filtered)}")
        logger.info(f"  - Failed conversions: {len(failed_conversions)}")

        # Show which courses had successful conversions
        successful_courses = set([course for _, course in successful_tasks])
        logger.info(f"  - Courses with successful conversions: {list(successful_courses)}")

        # Show recent past assignments that were filtered
        if past_assignments_filtered:
            logger.info(f"\n🕒 Recent Past Assignments Filtered:")
            # Sort by due date descending (most recent first)
            sorted_past = sorted(past_assignments_filtered, key=lambda x: x[2], reverse=True)
            for assignment_name, course_name, due_date in sorted_past[:10]:  # Show last 10
                logger.info(f"  - '{assignment_name}' ({course_name}) - Due: {due_date}")

    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_specific_course_processing())