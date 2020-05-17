#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

#include <seccomp.h> /* libseccomp */

char* unable_to_compile = "{\"passed\": false, \"message\": \"Unable to compile.\"}\n";
char* failed_test_cases = "{\"passed\": false, \"message\": \"Failed test cases.\"}\n";
char* secomp_add_fail = "{\"passed\": false, \"message\": \"seccomp_rule_add failed.\"}\n";
char* secomp_load_fail = "{\"passed\": false, \"message\": \"seccomp_load failed.\"}\n";

void write_out(char* message)
{
   write(1, message, strlen(message));
}

void json_output(char* message, char* passed, int exit_code)
{
   printf("{\"passed\": %s, \"message\": \"%s\"}\n", passed, message);
   exit(exit_code);
}

void json_fail(char* message, int exit_code)
{
   json_output(message, "false", exit_code);
}

void json_success(char* message, int exit_code)
{
   json_output(message, "true", exit_code);
}

void cleanup()
{
   write_out(failed_test_cases);
   kill(0, 9);
}

void do_seccomp()
{
   scmp_filter_ctx ctx;
   int rc = 0;
   ctx = seccomp_init(SCMP_ACT_KILL); // default action: kill

   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(rt_sigreturn), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(read), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(write), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(open), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(close), 0);   
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(execve), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(brk), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(arch_prctl), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(uname), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(readlink), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(access), 0);
   rc += seccomp_rule_add(ctx, SCMP_ACT_ALLOW, SCMP_SYS(exit_group), 0);

   if (rc != 0)
   {
      write_out(secomp_add_fail);
      exit(-2);
   }
   
   rc = seccomp_load(ctx);
   if (rc != 0)
   {
      write_out(secomp_load_fail);
      exit(-3);
   }

}

int main(int argc, char** argv)
{
   // set up the timer
   signal(SIGALRM, cleanup);
   alarm(2);

   struct stat file_stat;
   int res = fstat(1, &file_stat);
   if (res != 0)
   {
      return -1;
   }

   if(!S_ISREG(file_stat.st_mode))
   {
      return -1;
   }

   // Compile the program
   res = system("/usr/bin/gcc -static -o ./submission ./submission.c");
   if (res != 0)
   {
      write_out(unable_to_compile);
      return -4;
   }

   // Run it
   int child = fork();
   if (child == 0)
   {
	  char* args[2];
	  args[0] = "./submission";
	  args[1] = NULL;

	  close(0);
	  close(1);
	  close(2);
	  close(3);
	  close(4);

	  // seccomp all the things
	  do_seccomp();

	  execve(args[0], args, NULL);
   }
   else
   {
	  wait(0);
      write_out(failed_test_cases);
      return 0;
   }
}
