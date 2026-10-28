void Demo_Foo__Hit(long param_1)
{
  float fVar1;
  
  if ((*(int *)(param_1 + 0x20) < 1) || (*(char *)(param_1 + 0x28) == '\0')) {
    return;
  }
  *(float *)(param_1 + 0x24) = 2.5;
  Demo_Foo__Log(param_1,PTR_STR_9_hit_msg_0123abcd);
}
